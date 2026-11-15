# Per-second motion table

Format of `analysis/<nn>-motion.md`, written by the `motion-analyst` agent. One reference video gives one file. Later stages (`hook-marketer`, `review-council`, `synthesizer`, `recreation-director`) read it as data.

The file is written in the language set in the user's `profile.md` (default Ukrainian). The column headers and section headings below are fixed and are written exactly as shown, in this order.

## Table

One row per second of the video (`t, с` = 0, 1, 2 ...). A cell with nothing to report holds `—`. Never leave a cell blank.

| # | Column | What goes in the cell |
|---|--------|-----------------------|
| 1 | `t, с` | Second of the video, integer. |
| 2 | `Шот` | Shot number and what is in frame (subject, framing: close-up, medium, wide). A cut starts a new shot number. |
| 3 | `Камера: рух` | Camera move: static, pan, tilt, push-in, pull-out, orbit, handheld shake, whip. |
| 4 | `Камера: швидкість` | Speed of that move: slow, medium, fast, snap. |
| 5 | `Перехід` | Transition into this second: hard cut, match cut, whip, zoom, glitch, dissolve, mask wipe, none. |
| 6 | `Motion-елементи` | Animated graphic elements: shapes, particles, lines, stickers, overlays, speed ramps, shake, flashes. |
| 7 | `3D-об'єкти` | 3D objects or 3D-looking elements in frame and how they move. |
| 8 | `UI-графіка` | Interface-like graphics: progress bars, counters, cursors, notification cards, callouts, screen recordings. |
| 9 | `Текст` | On-screen text exactly as shown (original language), with position and size class. |
| 10 | `Поява тексту` | How the text enters and leaves: pop, slide, typewriter, word by word, fade, scale bounce. |
| 11 | `Easing` | Observed motion curve: linear, ease-in, ease-out, ease-in-out, overshoot or bounce, snap. |
| 12 | `Звуковий акцент` | Sound event on this second (hit, whoosh, riser, beat drop, voice word, silence), taken from the transcript or an audio cue, not guessed from the picture. |
| 13 | `Як відтворити` | One line for a motion designer: how to rebuild it (tool-agnostic: keyframes, durations in frames at 30 fps, easing). |
| 14 | `Кадр-доказ` | The frame that shows this row: frame file name (for example `f_0004.jpg`) or timestamp (`00:04.0`). Required in every row. |

Rules for the table:

- Every row cites an evidence frame in column 14. A row without a frame is not allowed.
- Each second is looked at separately. Do not copy the previous row forward without looking at the frame of this second.
- If a cell cannot be established from the frames, write `—` and list the question under `Чого не видно з кадрів`.
- Easing, speeds and durations are estimates from frame differences. Say `приблизно` or give a range when the sampling is coarse.

## Sections after the table

Exactly these three headings (level 2), in this order.

1. `Ритм монтажу` - shot lengths in seconds, in order (for example `Шот 1: 1.5 с, Шот 2: 0.8 с`), average shot length, and the number of cuts.
2. `Три прийоми, які варто взяти` - exactly three numbered techniques worth borrowing, each with the seconds where it appears and one line on how to rebuild it.
3. `Чого не видно з кадрів` - what the analyst could not establish from the frames (audio-only facts, hidden motion between sampled frames, unreadable text, true easing curves). Anything not established from a frame goes here and not into the table. If nothing is missing write `—`.

## Minimal example

```
| t, с | Шот | Камера: рух | Камера: швидкість | Перехід | Motion-елементи | 3D-об'єкти | UI-графіка | Текст | Поява тексту | Easing | Звуковий акцент | Як відтворити | Кадр-доказ |
|------|-----|-------------|-------------------|---------|-----------------|------------|------------|-------|--------------|--------|-----------------|---------------|------------|
| 0 | 1: крупний план, продукт | push-in | повільна | — | спалах білого | — | — | "СТОП" | pop | ease-out | удар | scale 100 -> 108 за 30 кадрів, ease-out | f_0000.jpg |
```
