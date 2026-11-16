# Review council roles

Used by the `review-council` agent. The same agent runs once per role, then once more to consolidate. A role run uses ONLY its own question list and writes only its own file. The skill gives the agent the role name exactly as written in the first column below.

| Role (exact name) | File written by the role run |
|-------------------|------------------------------|
| `Маркетолог` | `review-marketer.md` |
| `Таргетолог` | `review-targetolog.md` |
| `SMM-фахівець` | `review-smm.md` |

The consolidating run writes `review.md`.

## Row format

Every finding is one row of this table, in a role file and in `review.md`:

`№ | Ролик | Таймкод | Що не так | Важливість (критично / важливо / дрібниця) | Як виправити | Хто помітив`

- `№`: running number in the file, starting at 1
- `Ролик`: the video number `nn` as in `approved.md`, or `власний` for the user's own video
- `Таймкод`: `00:02.4` or an interval `00:00–00:03`; `весь ролик` when it applies to the whole video
- `Що не так`: the problem in one sentence, naming the evidence (frame, transcript line, section of the analysis)
- `Важливість`: exactly one of `критично`, `важливо`, `дрібниця`. `критично` means the video would be blocked, hidden, misleading or fails its main job. `важливо` means it clearly costs views, clarity or conversion. `дрібниця` means polish
- `Як виправити`: one concrete action
- `Хто помітив`: the role name; in `review.md` all roles that raised it, separated by a comma

A role also writes one line after the table, `Що в порядку`, naming up to three things the video does well from its point of view. A role that finds nothing writes the table header and one row with `—` in every cell except `Що не так`, which says what was checked.

## Role `Маркетолог`

Questions, in this order:

1. Offer. What exactly does the viewer get or learn, and is it stated by second 3? Who is it for?
2. Hook. Does the first 3 seconds create a reason to keep watching (curiosity gap, a promise, a pattern break, a conflict)? Is it the same promise the video then pays off?
3. Structure. Are there dead seconds, a sagging middle, a payoff that comes too late or too early? Is there a loop or a reason to rewatch?
4. Call to action. Is there one clear action, placed after value, matching the offer? Is it too many asks?
5. Message fit. Does the video suit the user's audience and style from `profile.md`?

## Role `Таргетолог`

Questions, in this order:

1. Ad suitability. Could this run as a paid creative as it is: one message, a clear product or benefit, a reason to click? What must change?
2. First 3 seconds with sound off. Without audio, does the picture and on-screen text alone carry the hook and the message? Are there captions?
3. Ad policy fit. Does anything in the video clash with the ad policies on the pages listed in `references/safe-zones.md` (restricted goods, misleading claims, before and after, personal attributes, music rights, watermarks of other apps)?
4. Test variants. Name 3 variants worth an A/B test: a different hook, a different first frame, a different call to action, a different length. Say what each one tests.
5. Format. Vertical, up to 90 seconds, readable at small size, text inside the safe zones for the ad placements.

## Role `SMM-фахівець`

Questions, in this order:

1. Platform requirements. Vertical 9:16, 1080×1920 or the same ratio, length up to 90 seconds, sound present, resolution not blurry. Anything the platforms reject?
2. Safe zones. Using `references/safe-zones.md`, does every piece of text sit inside the margins on Instagram Reels, TikTok and YouTube Shorts? Use the `Безпечні зони` section of the marketing analysis and check it against the frames. Say which numbers are unofficial.
3. Caption. Is the post caption (if known) short, with the keyword and the call to action in the first line?
4. Hashtags. Number, relevance to the topic and the platform; no banned or spammy tags.
5. Cover. Is there a frame that works as a cover and reads at small size and in a profile grid crop?
6. Reach risk. Visible watermarks of other apps, reposts of unchanged content, restricted topics, unlabelled realistic AI content, engagement bait, low quality. Name the platform page that backs each risk.
