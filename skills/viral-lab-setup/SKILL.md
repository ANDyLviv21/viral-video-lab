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

## 3. Check the profile

Look for `profile.md` in the user's current working folder (not inside the plugin). If it exists, read it and take the report language from the "Мова звітів" section (default Ukrainian).

If it is missing, offer to create it from `../../config/profile.example.md`. With the user's agreement, ask about the sections one by one (Тематика, Аудиторія, Стиль, Персонаж, Платформи, Мова звітів, Чого уникати), then write `profile.md` into the working folder.

## 4. Report

Write the report in the language from `profile.md` (default Ukrainian). Group it as: required and missing, optional and missing, checked manually (connectors, credits), profile status. For each missing item say what it is, which stages it affects, and give its `install_hint`.

## Rules

- Do not install or change anything on your own. Show the install command and ask first.
- Do not update already installed programs without consent.
- Never print or store keys or tokens.
