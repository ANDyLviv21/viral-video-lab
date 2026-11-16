# Recreation engines

Used by the `synthesizer` (section `Чим збирати`), the `recreation-director` (choice of the engine) and the `viral-recreate` skill (which third-party skills to run). Third-party skills run in the main conversation (method B in `run-layout.md`); agents receive only the resulting files.

| Need | Engine | Notes |
|------|--------|-------|
| Default | HyperFrames: HTML and GSAP, local render | Free, local. Run through the HyperFrames skills (`/hyperframes`, `/hyperframes-cli`). Vertical 1080×1920 composition, up to 90 seconds. Never the hosted HyperFrames connector: it is not local and may cost money |
| A video driven by data, or React components needed | Remotion | Run through the Remotion skills (`/remotion-best-practices`). Local render |
| 3D object in frame | `/threejs` | A Three.js scene rendered as part of the HyperFrames or Remotion project |
| A complex 3D scene | Blender | Through the Blender skills and the Blender connector. Render locally |
| Generated frames or clips | `/video-prompting` writes the prompts, `/higgsfield` makes the generation | PAID. Never started without Stop 3: the sum is shown and the user agrees first |
| Footage the user shot | `/video-editing` | Cutting, structure and polish of real footage |
| Subtitle timing | Whisper, local | Word timing from the voice track; no cloud transcription |
| Final export | `/ffmpeg-skill` | 1080×1920 mp4 per platform, with the checks in `viral-recreate` |

## Choosing

1. Free and local first. If the idea can be built in HyperFrames without a generated frame, it is built there.
2. A generated frame is chosen only when the idea cannot work without it. Then the paid item is listed in the variant, and Stop 3 applies at every point before the paid action.
3. Mixed builds are fine: `draft.mp4` can be rendered with placeholder cards (a plain card with the text `кадр буде згенеровано`) before any paid generation, so the user sees the timing and decides on the spend with the draft in hand.

## Safe zones in the build

The subtitle band and the hook-text area come from `safe-zones.md`. The director uses the row of the chosen platform when the video goes to one platform, and the cross-platform subtitle band otherwise, and writes which row it relied on in the header of `storyboard.md`. Almost every row is marked «неофіційне»: it is the best available guidance, not a platform rule, and `qc.md` repeats the row and its mark.
