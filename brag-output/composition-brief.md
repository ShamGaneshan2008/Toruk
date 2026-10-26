# Hyperframes Composition Brief: Toruk-LM

## Objective
Create a 20-second cinematic launch-style research trailer for Toruk-LM, grounded in its actual code, UI, README, architecture, and saved evaluation artifacts.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape, 1920x1080
- Duration: 20 seconds

## Source material
- Project root: `C:\Users\susee\VScode Project\Toruk`
- Primary files read: `README.md`, `docs/architecture.md`, `docs/milestones.md`, `docs/experiments.md`, `src/toruk_lm/chat_ui.html`, `artifacts/minimal-lm-demo-001/eval/predictions.json`
- Product name: Toruk-LM
- Tagline, verbatim: “Remember what matters. Revise what changed.”
- Key UI: dark local experimental chat page; show the notice and text-continuation flow.
- Saved output to reproduce: prefix `abc abc abc abc abc abc abc abc ` and generated `abc abc abc abc `.

## Creative direction
- Tone preset: cinematic
- Direction: restrained scientific trailer with editorial type and deep-blue lighting
- Hook: “WHAT SHOULD A MODEL REMEMBER? WHEN FACTS CHANGE?”
- Outro: tagline, Toruk-LM, research prototype
- Avoid generic marketing phrases, invented results, and any claim of demonstrated memory benefit.

## Visual identity
- Background `#101722`; text `#edf3fa`; focus accent `#89c5fa`; panel blue `#29445e`
- System sans display and body fonts, matching the local UI
- Recreate actual local interface language and shapes.
- LOOK: dark blue research instrument, generous negative space, luminous hairlines, restrained camera depth, crisp white type.

## Storyboard
Use `../brag-plan.md` as the creative contract.
1. The question — 3s — two-clause hook.
2. Revise, preserve — 4s — illustrative Mira update, explicitly a research objective.
3. The foundation — 4s — verified causal LM, prototype memory, implemented scoring.
4. The real experiment — 5s — recreated local page and saved text continuation.
5. Name and horizon — 4s — tagline and research status.

## Audio
- Low cinematic bed: bundled vol-12 Sascha Ende track, copied into `composition/assets/music/`.
- Cue preset: bundled vol-12, ~110 BPM; optional strong moments 8.74s and 17.47s.
- Quiet, warm SFX on title, correction, send, and closing logo.
- Audio-reactive extraction was unavailable because the project Python interpreter is inaccessible in this environment. The halo uses authored, music-cued motion instead.
- Copy chosen SFX into `composition/assets/` before render.
- Music credit for public sharing: Sascha Ende, ende.app (CC BY 4.0).

## Hyperframes instructions
Follow the installed brag skill's Hyperframes workflow: composition contract, format, motion, look, registry, media-use, CLI check and render. No voiceover. The finished video must show real Toruk UI/copy, readable text, and accurate research status. Run `hyperframes check` before final render. Keep all files under `brag-output/`.
