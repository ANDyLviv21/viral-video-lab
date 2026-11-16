---
name: viral-lab-setup
description: Checks and prepares the viral-video-lab environment on a new PC (dependencies, connectors and the channel profile). Use when the user says перевір залежності viral lab, налаштуй viral-video-lab, viral lab setup or check viral lab dependencies.
---

# Viral Lab Setup

Check what the viral-video-lab plugin needs on this PC and report what is missing and why it matters. Never install anything without the user's explicit consent.

Paths below are relative to this skill's base directory. Pipeline stages: 0 brief, 1 trend scouting, 2 top-5 selection and download, 3 motion analysis, 4 marketing analysis, 5 review council, 6 synthesis, 7 recreation, 8 quality control.

## 1. Run the dependency checker

Run:

```
py -3.12 <skill base dir>/../../scripts/check_deps.py --manifest <skill base dir>/../../config/dependencies.json
```

Add `--json` if you need machine-readable output. Exit code 0 means every required dependency is present; 1 means a required one is missing. The manifest is `../../config/dependencies.json`; each dependency is explained in `../../DEPENDENCIES.md`.

## 2. Check connectors

The script cannot see connectors (status `manual`). Check them yourself. Connector tool names carry a per-machine prefix, so never use a full hard-coded name. Find the tool whose name ENDS with:

- `v1_account_credit_balance` for ScrapeCreators
- `vidiq_balance` for vidIQ

If a tool is deferred, load it first (for example with ToolSearch, searching by that ending). Call it and show the user the remaining credits. At least one of the two connectors is required (stage 1). If neither is found, tell the user to enable ScrapeCreators or vidIQ in the connector settings of the app.

## 3. Check how `/watch` is configured

`/watch` is the one dependency that needs CONFIGURING and not just installing, and it is the key tool of this plugin: the per-second motion table, the hook analysis and the quality check all rest on what it returns. Step 1 only reports that the skill exists.

Find its own setup script: the installed skill lives in the user's Claude skills folder, so the script is `setup.py` inside the `scripts` folder of the installed `watch` skill, that is `<WATCH>` + `/setup.py`, where `<WATCH>` is `<skills folder>/watch/scripts` and `<skills folder>` is the `skills` folder of the user's Claude home (`~/.claude/skills` on this machine). Derive the path from that folder; never hardcode a user name or a drive letter. If the file is not there, `/watch` is not installed: say so, repeat its `install_hint` from step 1, and skip to step 4.

Run ONLY the read-only query, with the Python interpreter the user has:

```
py -3.12 "<WATCH>/setup.py" --json
```

`--json` reports the state and changes nothing. **Never run that script with no arguments, with `--backend`, `--detail`, `--engine` or `--install-whisperx` in this step**: those write configuration, and `--install-whisperx` downloads about 1.5 GB. If something needs installing or configuring, show the exact command and ask first, as the rules of this skill require everywhere else.

Read these fields of the answer: `can_proceed`, `engine` (the one actually in force), `configured_engine` (the saved choice), `gemini_key_present` (a BOOLEAN, never a key), `setup_complete`, `whisper_backend`, `backend_ready`, `watch_detail`, and `missing_binaries`.

Then report, in the user's language:

1. **Which engine is active, and what that means for what leaves the machine.** `engine: gemini` means Google's video model watches the WHOLE video including its audio: a YouTube URL is sent to Google, and any other video, a local file included, is uploaded to Google's Files API and deleted after the answer. `engine: local` means yt-dlp and ffmpeg run here and nothing about the video reaches Google. Say it in one plain line, the way the stage skills say it before their first call (`The /watch handoff`, step 0, in `../../references/run-layout.md`).
2. **What the report can and cannot contain on that engine.** On `local`, quote the block `Що локальний рушій не дає` of `../../references/watch-questions.md` as it stands there: the `Звуковий акцент` column, the sound part of the hook and the beat question have no evidence, because frames plus a speech transcript carry no hits, whooshes, risers or beat.
3. **What is missing.** `can_proceed: false` or a non-empty `missing_binaries` on the `local` engine means `ffmpeg` or `yt-dlp` is absent and the local route cannot run at all. On the `gemini` engine those binaries do not block a YouTube URL but are still needed for every other URL and for any `--engine local` call.
4. **The transcript situation, plainly.** When `setup_complete` is false and `backend_ready` is false, a video WITHOUT native captions gets no transcript at all — and most Reels and TikToks have none. Do not soften this: without a transcript the speech evidence of the whole run is empty.

Then give the user the three routes, with what each costs them:

- **`gemini` (recommended; Андрій's standing choice).** A free key from https://aistudio.google.com/apikey. The whole video, audio included, is watched by Google's model, so this is the ONLY route that yields sound accents, music and the beat, and the only route that fills the `Звуковий акцент` column and the sound part of the hook. The cost is privacy: the video or its URL goes to Google. Configured with `setup.py --engine gemini`, which is `/watch`'s own command and the only thing that should ever touch the key.
- **`whisperx`.** Local speech recognition, no key, audio never leaves the machine. A one-time download of about 1.5 GB and roughly 3 GB of free disk; CPU transcription takes minutes per video. It gives speech only: still no music, no hits, no beat. Configured with `setup.py --backend whisperx`, which runs the managed installer — ask before suggesting it and never run it here.
- **Captions only (`--backend none`).** Nothing is downloaded and nothing is uploaded, and a video without captions has no transcript. Acceptable only if the user knows that.

The key itself: it lives in `/watch`'s own private config file, the `.env` inside the `watch` folder of the user's `~/.config`, and `/watch`'s setup writes it there. Never print it, never echo it, never put it in a command line, never template it into a file and never ask for it in chat. If it is missing, `gemini_key_present` is false: say that the key is missing, point at https://aistudio.google.com/apikey and at `setup.py --engine gemini`, and let `/watch`'s own setup handle the rest.

## 4. Check the profile

Look for `profile.md` in the user's current working folder (not inside the plugin). If it exists, read it and take the report language from the "Мова звітів" section (default Ukrainian).

If it is missing, offer to create it from `../../config/profile.example.md`. With the user's agreement, ask about the sections one by one (Тематика, Аудиторія, Стиль, Персонаж, Платформи, Мова звітів, Чого уникати), then write `profile.md` into the working folder.

## 5. Report

Write the report in the language from `profile.md` (default Ukrainian). Group it as: required and missing, optional and missing, checked manually (connectors, credits), the `/watch` engine and what it means for the sound columns, profile status. For each missing item say what it is, which stages it affects, and give its `install_hint`.

## Rules

- Do not install or change anything on your own. Show the install command and ask first.
- Do not update already installed programs without consent.
- Never print or store keys or tokens.
