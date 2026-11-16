# Recreation engines

Used by the `synthesizer` (section `Чим збирати`), the `recreation-director` (choice of the engine) and the `viral-recreate` skill (which third-party skills to run). Third-party skills run in the main conversation (method B in `run-layout.md`); agents receive only the resulting files.

| Need | Engine | Notes |
|------|--------|-------|
| Default | HyperFrames: HTML and GSAP, local render | Free, local. Run through the HyperFrames skills (`/hyperframes`, `/hyperframes-cli`). Vertical 1080×1920 composition, up to 90 seconds. Never the hosted HyperFrames connector: it is not local and may cost money |
| A video driven by data, or React components needed | Remotion | Run through the Remotion skills (`/remotion-best-practices`). Local render |
| 3D object in frame | `/threejs` | A Three.js scene rendered as part of the HyperFrames or Remotion project |
| A complex 3D scene | Blender | The `viral-recreate` skill runs it in the main conversation (Blender skills and connector), renders locally into `recreation/assets/`, and the director places the files in the project. The director cannot run Blender itself |
| Generated frames or clips | `/video-prompting` and `/higgsfield` write the prompts; NOTHING on this machine generates the frames | PAID and done by hand. Both skills only produce prompt text: `/higgsfield` writes prompts for the higgsfield.ai web platform, which Андрій drives himself in the browser, pays for himself and brings back as files. The plugin therefore cannot measure or cap this spend: `limits.generation` is ADVISORY, a figure to show at Stop 3 and compare against what Андрій reports, not a ceiling the plugin can enforce. If a paid generator connector is enabled in the session, the skill may submit items through it one at a time after a Stop 3 yes, and only then is the spend measurable and recorded in `run.json.credits.generation`. Never started without Stop 3: the sum is shown and the user agrees first |
| Footage the user shot | `/video-editing` | Cutting, structure and polish of real footage |
| Subtitle timing | Whisper, local | Word timing from the voice track. `/watch` is called with `--engine local` AND an explicit local speech choice (`--whisper whisperx`, or `--no-whisper` when no local model is installed): `--engine local` alone does not rule out a cloud API, because the installed skill still accepts `--whisper groq|openai` and a saved `auto` backend looks for a Groq or OpenAI key |
| Final export | `/ffmpeg-skill` | 1080×1920 mp4 per platform, with the checks in `viral-recreate` |

Paid generation is not available to the `recreation-director` agent at all: it describes what it needs in `recreation/paid-request.md`, and the skill runs the generation after the user agrees.

## Choosing

1. Free and local first. If the idea can be built in HyperFrames without a generated frame, it is built there.
2. A generated frame is chosen only when the idea cannot work without it. Then the paid item is listed in the variant, and Stop 3 applies at every point before the paid action.
3. Mixed builds are fine: `draft.mp4` can be rendered with placeholder cards (a plain card with the text `кадр буде згенеровано`) before any paid generation, so the user sees the timing and decides on the spend with the draft in hand.

## Safe zones in the build

The subtitle band and the hook-text area come from `safe-zones.md`. The director uses the row of the chosen platform when the video goes to one platform, and the cross-platform subtitle band otherwise, and writes which row it relied on in the header of `storyboard.md`. Almost every row is marked «неофіційне»: it is the best available guidance, not a platform rule, and `qc.md` repeats the row and its mark.
