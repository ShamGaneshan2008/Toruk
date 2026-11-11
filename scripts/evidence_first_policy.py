"""Bounded research-only policy. No production imports this module.

The answer interface contains Q, fitted source bytes and content-free metadata,
never history, a selector, pre-fit text or an arbitrary source lookup callback.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass

MAX_TURNS = 64
MAX_BYTES = 16384


class IntegrityError(ValueError):
    """Invalid provenance; callers must halt rather than answer."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Turn:
    id: str
    role: str
    chronology: int
    length: int
    sha256: str
    selected: bool
    fitted: bool


@dataclass(frozen=True)
class Interval:
    turn: str
    start: int
    end: int


@dataclass(frozen=True)
class Source:
    interval: Interval
    raw: bytes
    revision: str
    turn_sha256: str


@dataclass(frozen=True)
class Manifest:
    revision: str
    turns: tuple[Turn, ...]
    question_sha256: str


@dataclass(frozen=True)
class View:
    question: str
    manifest: Manifest
    sources: tuple[Source, ...]


@dataclass(frozen=True)
class Coverage:
    scope: tuple[str, ...]
    omitted: tuple[Interval, ...]
    unparsed: tuple[Interval, ...]

    @property
    def complete(self) -> bool:
        return not self.omitted and not self.unparsed


def make_view(messages: list[dict[str, str]], selected: list[int], fitted: list[int]) -> View:
    """Selection/fitting boundary only: hash H, then drop every omitted byte."""
    if not 2 <= len(messages) <= MAX_TURNS:
        raise IntegrityError("history turn bound")
    if messages[-1]["role"] != "user":
        raise IntegrityError("question must be the last user turn")
    if sum(len(m["content"].encode("utf-8")) for m in messages) > MAX_BYTES:
        raise IntegrityError("history byte bound")
    for indices in (selected, fitted):
        if indices != sorted(set(indices)) or not indices or indices[-1] != len(messages) - 1:
            raise IntegrityError("ordered source IDs including Q required")
        if indices[0] < 0 or indices[-1] >= len(messages):
            raise IntegrityError("source ID outside history")
    if not set(fitted) <= set(selected):
        raise IntegrityError("fit may only remove selected turns")
    revision = digest(json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode())
    turns = tuple(
        Turn(
            f"m{i}",
            m["role"],
            i,
            len(m["content"].encode()),
            digest(m["content"].encode()),
            i in selected,
            i in fitted,
        )
        for i, m in enumerate(messages[:-1])
    )
    sources = tuple(
        Source(
            Interval(t.id, 0, t.length),
            messages[t.chronology]["content"].encode(),
            revision,
            t.sha256,
        )
        for t in turns
        if t.fitted
    )
    return View(
        messages[-1]["content"],
        Manifest(revision, turns, digest(messages[-1]["content"].encode())),
        sources,
    )


def gaps(turn: str, length: int, intervals: tuple[Interval, ...]) -> tuple[Interval, ...]:
    cursor = 0
    missing = []
    for part in sorted((p for p in intervals if p.turn == turn), key=lambda p: p.start):
        if not 0 <= part.start <= part.end <= length:
            raise IntegrityError("invalid UTF-8 byte interval")
        if part.start > cursor:
            missing.append(Interval(turn, cursor, part.start))
        cursor = max(cursor, part.end)
    if cursor < length:
        missing.append(Interval(turn, cursor, length))
    return tuple(missing)


def validate_view(view: View) -> None:
    manifest = view.manifest
    if digest(view.question.encode()) != manifest.question_sha256:
        raise IntegrityError("question/revision mismatch")
    turns = {t.id: t for t in manifest.turns}
    if len(turns) != len(manifest.turns) or len(turns) >= MAX_TURNS:
        raise IntegrityError("duplicate or excessive manifest turns")
    if any(
        t.id != f"m{i}"
        or t.chronology != i
        or t.length < 0
        or t.role not in {"user", "assistant", "system"}
        or (t.fitted and not t.selected)
        for i, t in enumerate(manifest.turns)
    ):
        raise IntegrityError("invalid role/chronology/selection metadata")
    if sum(t.length for t in manifest.turns) + len(view.question.encode()) > MAX_BYTES:
        raise IntegrityError("manifest byte bound")
    for source in view.sources:
        t = turns.get(source.interval.turn)
        if (
            t is None
            or not t.fitted
            or source.revision != manifest.revision
            or source.turn_sha256 != t.sha256
            or len(source.raw) != source.interval.end - source.interval.start
        ):
            raise IntegrityError("source provenance mismatch")
        gaps(t.id, t.length, (source.interval,))
        source.raw.decode("utf-8", errors="strict")
    for t in manifest.turns:
        pieces = sorted(
            (s for s in view.sources if s.interval.turn == t.id), key=lambda s: s.interval.start
        )
        if any(a.interval.end > b.interval.start for a, b in zip(pieces, pieces[1:], strict=False)):
            raise IntegrityError("overlapping source intervals")
        if pieces and not gaps(t.id, t.length, tuple(s.interval for s in pieces)):
            if digest(b"".join(s.raw for s in pieces)) != t.sha256:
                raise IntegrityError("source bytes/revision mismatch")


def assess_coverage(view: View, scope: tuple[str, ...], parsed: tuple[Interval, ...]) -> Coverage:
    """Absence needs BOTH raw-byte coverage and recognized-parser coverage.

    A scope is declared before searching; it cannot be inferred from a match or
    reduced to selected turns. Unknown IDs are invalid scopes, never empty ones.
    The parser, not annotations or an LM, supplies recognized intervals.
    """
    validate_view(view)
    turns = {t.id: t for t in view.manifest.turns}
    if not scope or len(set(scope)) != len(scope) or not set(scope) <= turns.keys():
        raise IntegrityError("nonempty finite scope with known turn IDs required")
    for p in parsed:
        if p.turn not in turns:
            raise IntegrityError("invalid parsed interval")
        gaps(p.turn, turns[p.turn].length, (p,))
        if not any(
            s.interval.turn == p.turn and s.interval.start <= p.start and s.interval.end >= p.end
            for s in view.sources
        ):
            raise IntegrityError("parser cannot cover unavailable bytes")
    raw = tuple(s.interval for s in view.sources)
    omitted = tuple(g for tid in scope for g in gaps(tid, turns[tid].length, raw))
    unparsed = tuple(g for tid in scope for g in gaps(tid, turns[tid].length, parsed))
    return Coverage(scope, omitted, unparsed)


# Deliberately small declared grammar, not a general natural-language parser.
# Values are literal double-quoted strings, without escapes or embedded quotes.
# Every nonblank line must be a declaration or the exact inert `No assertion.`.
NAME = r"[A-Za-z][A-Za-z0-9_-]*(?: [A-Za-z0-9_-]+)*"
FACT = re.compile(
    rf"(?P<correction>Correction: )?(?P<entity>{NAME})'s (?P<field>{NAME}) "
    r'is (?P<negative>not )?"(?P<value>[^"\r\n]*)"\.'
)
BINDING = rf"(?P<entity>{NAME})'s (?P<field>{NAME})"
# Two separate patterns avoid duplicate named groups in a regular expression.
GET = re.compile(rf"What is {BINDING}\?")
COPY = re.compile(rf"Copy {BINDING}\.")
COMBINE = re.compile(rf"Combine (?P<left>{NAME}'s {NAME}) and (?P<right>{NAME}'s {NAME})\.")
SCOPE = re.compile(r"In turns (?P<ids>m\d+(?:,m\d+)*): (?P<request>.+)")
PRONOUNS = frozenset({"it", "its", "that", "this", "they", "them", "their"})
QUALIFIERS = frozenset(
    {
        "latest",
        "current",
        "previous",
        "original",
        "earliest",
        "recent",
        "former",
        "before",
        "after",
        "since",
        "until",
        "only",
        "except",
        "rather",
        "not",
        "and",
        "or",
    }
)
SUPPORTED = "supported"
ABSENT = "absent-in-complete-scope"
INCOMPLETE = "coverage-incomplete"
AMBIGUOUS = "ambiguous/conflicting"


@dataclass(frozen=True)
class Provenance:
    revision: str
    turn: str
    role: str
    chronology: int
    turn_sha256: str
    start: int
    end: int


@dataclass(frozen=True)
class Fact:
    entity: str
    field: str
    negative: bool
    correction: bool
    source: Provenance


@dataclass(frozen=True)
class Request:
    scope: tuple[str, ...]
    bindings: tuple[tuple[str, str], ...]
    synthesis: bool


@dataclass(frozen=True)
class Answer:
    payload: str
    state: str
    route: str
    reason: str
    scope: tuple[str, ...]
    coverage: Coverage | None
    sources: tuple[Provenance, ...] = ()
    corrections: tuple[tuple[Provenance, Provenance], ...] = ()
    generated: str | None = None
    parsed_bytes: int = 0


def bind_request(view: View) -> Request | None:
    question = view.question
    scope = tuple(t.id for t in view.manifest.turns)
    scoped = SCOPE.fullmatch(question)
    if scoped:
        scope = tuple(scoped["ids"].split(","))
        question = scoped["request"]
    if not scope or len(set(scope)) != len(scope):
        return None
    if not set(scope) <= {t.id for t in view.manifest.turns}:
        return None
    direct = GET.fullmatch(question) or COPY.fullmatch(question)
    if direct:
        # Unsupported constraints cannot become unknown literal field names
        # and then produce a false absence certificate.
        if QUALIFIERS.intersection(direct["field"].casefold().split()):
            return None
        return Request(scope, ((direct["entity"].casefold(), direct["field"].casefold()),), False)
    combine = COMBINE.fullmatch(question)
    if combine:
        bindings = tuple(tuple(combine[k].casefold().split("'s ")) for k in ("left", "right"))
        if any(QUALIFIERS.intersection(field.split()) for _, field in bindings):
            return None
        return Request(scope, bindings, True)
    return None


def parse_sources(view: View) -> tuple[tuple[Fact, ...], tuple[Interval, ...]]:
    """Only complete recognized lines count as parsed, including their newlines."""
    facts = []
    parsed = []
    metadata = {t.id: t for t in view.manifest.turns}
    for source in view.sources:
        offset = source.interval.start
        for raw_line in source.raw.splitlines(keepends=True):
            line = raw_line.decode("utf-8").rstrip("\r\n")
            match = FACT.fullmatch(line)
            interval = Interval(source.interval.turn, offset, offset + len(raw_line))
            if not line.strip() or line == "No assertion.":
                parsed.append(interval)
            elif (
                match
                and metadata[interval.turn].role == "user"
                and match["entity"].casefold() not in PRONOUNS
            ):
                parsed.append(interval)
                start = offset + len(line[: match.start("value")].encode())
                end = start + len(match["value"].encode())
                t = metadata[interval.turn]
                facts.append(
                    Fact(
                        match["entity"].casefold(),
                        match["field"].casefold(),
                        bool(match["negative"]),
                        bool(match["correction"]),
                        Provenance(
                            view.manifest.revision, t.id, t.role, t.chronology, t.sha256, start, end
                        ),
                    )
                )
            offset += len(raw_line)
    return tuple(facts), tuple(parsed)


def reslice(view: View, provenance: Provenance) -> str:
    """Never opens history: the only possible read is from an already-fitted slice."""
    t = next((t for t in view.manifest.turns if t.id == provenance.turn), None)
    if (
        t is None
        or provenance.revision != view.manifest.revision
        or (provenance.role, provenance.chronology, provenance.turn_sha256)
        != (t.role, t.chronology, t.sha256)
    ):
        raise IntegrityError("copy provenance mismatch")
    for source in view.sources:
        if (
            source.interval.turn == t.id
            and source.interval.start <= provenance.start <= provenance.end <= source.interval.end
        ):
            raw = source.raw[
                provenance.start - source.interval.start : provenance.end - source.interval.start
            ]
            return raw.decode("utf-8", errors="strict")
    raise IntegrityError("copy interval unavailable")


def resolve(
    view: View, facts: tuple[Fact, ...], binding: tuple[str, str]
) -> tuple[str, Provenance | None, tuple[tuple[Provenance, Provenance], ...], str]:
    current = None
    links: list[tuple[Provenance, Provenance]] = []
    conflict = False
    negatives: set[str] = set()
    for fact in sorted(facts, key=lambda f: (f.source.chronology, f.source.start)):
        if (fact.entity, fact.field) != binding:
            continue
        if fact.negative:
            negatives.add(reslice(view, fact.source))
            if current and reslice(view, current) == reslice(view, fact.source):
                conflict = True
        elif fact.correction:
            if current is None:
                return INCOMPLETE, None, (), "correction antecedent unavailable"
            links.append((current, fact.source))
            current, conflict = fact.source, False
            negatives.clear()
        elif current is None:
            current = fact.source
        elif reslice(view, current) != reslice(view, fact.source):
            conflict = True
    if current and reslice(view, current) in negatives:
        conflict = True
    if conflict or (negatives and current is None):
        return AMBIGUOUS, None, tuple(links), "conflicting or negative-only requested field"
    if current:
        return SUPPORTED, current, tuple(links), "unique supported requested field"
    return ABSENT, None, tuple(links), "no requested field in complete parsed scope"


def answer(
    view: View, *, token_count: Callable[[str], int], generate: Callable[[], str] | None = None
) -> Answer:
    """Same policy for either selector; synthesis uses the caller's unchanged LM prompt.

    Synthesis is bounded to an ordered combination of two literal premises.
    A generated answer is supported only if it is exactly their conjunction
    using a declared separator. Open-ended entailment is deliberately unsupported.
    """
    validate_view(view)
    request = bind_request(view)
    if request is None:
        return Answer(
            "UNKNOWN", INCOMPLETE, "abstain", "unsupported request/scope grammar", (), None
        )
    facts, parsed = parse_sources(view)
    coverage = assess_coverage(view, request.scope, parsed)
    count = sum(i.end - i.start for i in parsed)

    def abstain(
        state: str, reason: str, sources: tuple[Provenance, ...] = (), generated: str | None = None
    ) -> Answer:
        return Answer(
            "UNKNOWN",
            state,
            "abstain",
            reason,
            request.scope,
            coverage,
            sources=sources,
            generated=generated,
            parsed_bytes=count,
        )

    if not coverage.complete:
        return abstain(INCOMPLETE, "omitted or unparsed scope bytes")
    if any(entity in PRONOUNS for entity, _ in request.bindings):
        return abstain(AMBIGUOUS, "unresolved reference")
    scoped_facts = tuple(f for f in facts if f.source.turn in request.scope)
    sources = []
    links = []
    for binding in request.bindings:
        state, source, corrections, reason = resolve(view, scoped_facts, binding)
        if state != SUPPORTED:
            return abstain(
                state, "missing synthesis premise: " + reason if request.synthesis else reason
            )
        assert source is not None
        sources.append(source)
        links.extend(corrections)
    provenance = tuple(sources)
    values = tuple(reslice(view, p) for p in provenance)
    generated = None
    if request.synthesis:
        if generate is None:
            return abstain(INCOMPLETE, "synthesis LM unavailable", provenance)
        generated = generate()
        # Exact permitted forms audit EVERY generated byte; citation IDs alone
        # cannot make a fabricated claim pass. No trim/normalization here.
        if generated not in {separator.join(values) for separator in ("; ", " and ", ", ", "\n")}:
            return abstain(AMBIGUOUS, "unsupported synthesis output", provenance, generated)
        payload, route = generated, "synthesis"
    else:
        payload, route = values[0], "copy"
    if token_count(payload) > 64:
        return abstain(INCOMPLETE, "64-token answer bound", provenance, generated)
    return Answer(
        payload,
        SUPPORTED,
        route,
        "source-linked " + route,
        request.scope,
        coverage,
        provenance,
        tuple(links),
        generated,
        count,
    )
