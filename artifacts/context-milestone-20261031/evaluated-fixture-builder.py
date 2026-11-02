"""Write disjoint synthetic development/final fixtures once, before evaluation."""

import json
from pathlib import Path

NOISE = [
    "I am planning a garden with herbs, vegetables, a winding path and a shaded bench.",
    "My workshop includes morning talks, a lunch break, afternoon practice "
    "and a closing discussion.",
    "A walking route passes a river, a museum, a busy market and a quiet library.",
    "The lunch recipe needs lentils, ginger, onions, tomatoes and some fresh bread.",
    "My office inventory includes pencils, notebooks, folders, calendars and a small lamp.",
]


def case(case_id, category, facts, query, accepted, forbidden, required):
    messages = []
    for text in [*facts, *NOISE]:
        messages.extend(
            [
                {"role": "user", "content": text},
                {"role": "assistant", "content": "Noted."},
            ]
        )
    messages.append({"role": "user", "content": query})
    return {
        "id": case_id,
        "category": category,
        "messages": messages,
        "accepted": accepted,
        "forbidden": forbidden,
        "required_evidence": [f"m{2 * i}" for i in required],
    }


def cases(prefix, n, values):
    code, old, new, color1, color2, owner, locker, depot = values
    return [
        case(
            f"{prefix}-recall-{n}",
            "long_range_recall",
            [f"The parcel tracking code is {code}."],
            "What is the parcel tracking code? Reply with only the code.",
            [code],
            [],
            [0],
        ),
        case(
            f"{prefix}-revision-{n}",
            "corrections",
            [
                f"The delivery day is {old}.",
                f"Correction: it is {new}.",
                "The delivery day label is printed on white paper.",
            ],
            "What is the delivery day now? Reply with only the day.",
            [new],
            [old],
            [0, 1],
        ),
        case(
            f"{prefix}-conflict-{n}",
            "conflicting_facts",
            [
                f"One note says the studio wall color is {color1}.",
                f"Another note says the studio wall color is {color2}. Neither note is confirmed.",
            ],
            "What is the studio wall color? Reply UNKNOWN if the notes conflict.",
            ["unknown", "conflict", "cannot determine", "don't know", "not enough information"],
            [color1, color2],
            [0, 1],
        ),
        case(
            f"{prefix}-irrelevant-{n}",
            "irrelevant_history",
            [f"My favorite notebook has the label {code}."],
            "Which planet is closest to the Sun? Reply with only the planet name."
            if n != 2
            else "What is 6 + 7? Reply with only the number.",
            ["mercury"] if n != 2 else ["13", "thirteen"],
            [],
            [],
        ),
        case(
            f"{prefix}-chain-{n}",
            "multi_hop_facts",
            [
                f"The camera belongs to {owner}.",
                f"{owner} uses locker {locker}.",
                f"Locker {locker} is at depot {depot}.",
                "Locker Varo is at depot Maple.",
            ],
            "At which depot is the camera owner's locker? Reply with only the depot.",
            [depot],
            ["maple"],
            [0, 1, 2],
        ),
        case(
            f"{prefix}-unknown-{n}",
            "unknown_answers",
            [f"My parcel tracking code is {code}."],
            "What is my childhood teacher's name? I have not provided it. "
            "Reply UNKNOWN if unknown.",
            [
                "unknown",
                "don't know",
                "do not know",
                "not provided",
                "haven't provided",
                "haven't told",
                "not specified",
                "cannot determine",
                "don't have",
            ],
            [],
            [],
        ),
    ]


def main():
    settings = {"max_new_tokens": 32, "temperature": 0, "top_p": 1}
    groups = {
        "dev": cases(
            "dev", 0, ("DEV-41", "Monday", "Friday", "blue", "red", "Davin", "Ralo", "Aspen")
        ),
        "final": [
            *cases(
                "final",
                1,
                ("YEW-83", "Wednesday", "Saturday", "cyan", "coral", "Nerin", "Talo", "Juniper"),
            ),
            *cases(
                "final",
                2,
                ("ELM-62", "Sunday", "Tuesday", "amber", "violet", "Sorin", "Bela", "Cedar"),
            ),
        ],
    }
    for split, rows in groups.items():
        path = Path(f"configs/context-eval-{split}-v1.json")
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite frozen fixture: {path}")
        path.write_text(
            json.dumps(
                {
                    "schema": "toruk-context-eval-v1",
                    "split": split,
                    "settings": settings,
                    "scoring": "casefolded word-boundary accepted phrase and no forbidden phrase; "
                    "unsupported = incorrect non-abstention. "
                    "Automatically flagged, manually review raw answers.",
                    "cases": rows,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
