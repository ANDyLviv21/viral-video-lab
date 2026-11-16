# Direction profile

Андрій works in several directions, not one niche, so the profile is TWO layers. This file is the one description of both: the template of the direction layer, the precedence rule every reader follows, and where a direction profile is written, saved and reused. Other files point here instead of repeating it.

## The two layers

| Layer | File | Holds | Who writes it |
|-------|------|-------|---------------|
| base | `profile.md` in the user's working folder, from `config/profile.example.md` | what does not change between directions: `Персонаж`, `Манера`, `Платформи` (priority), `Мова звітів`, `Чого уникати` | `viral-lab-setup`, with the user |
| direction | `direction-profile.md` in the run folder, from the template below | what belongs to THIS direction: audience, search language, tone, the norms of the niche, the platforms that matter for it, what to avoid in it | `viral-scout` at the brief step (stage 0), with the user |

## Precedence

This is the ONE place the rule is written. Every skill and agent that reads a profile follows it:

1. The direction profile of the run is the PRIMARY source. Where it and the base profile disagree, the direction profile wins.
2. A section the direction profile does not fill falls back to the base profile.
3. **Exception: the report language always comes from the base profile**, section `Мова звітів` (Ukrainian when it is missing or unreadable). A direction profile never changes it, and a reader that is handed only a direction profile still writes in the base language.
4. A run with no direction profile uses the base profile alone, and the report says so in one line: `профілю напряму немає, використано базовий профіль`.
5. If neither file is readable, write in Ukrainian and say which file was missing.

Agents never look for either file themselves: the orchestrating skill hands them absolute paths (method B, `run-layout.md`).

## Template

A direction profile is written in the report language, one line or a few per section, all eight headings present. A section the user does not care about says `не визначено` — never a guess dressed as a fact.

```
# Профіль напряму: <назва напряму>

## Напрям
Коротка назва й суть напряму. Наприклад: «побутова техніка — огляди й лайфхаки».

## Тематика
Теми й ключові слова цього напряму. Наприклад: «пилососи, мультиварки, дрібна кухонна техніка».

## Аудиторія
Хто дивиться саме це: вік, країна, мова, інтереси, болі. Наприклад: «25–45, Україна, українська, обирають техніку до 10 тис. грн».

## Мова пошуку
Мова контенту, який шукаємо в цьому напрямі (не мова звітів). Наприклад: «українська та англійська».

## Стиль і тон
Кольори, шрифти, темп монтажу, настрій саме цього напряму. Наприклад: «теплі кольори, швидкий темп, спокійний тон без хайпу».

## Норми ніші
Як тут прийнято знімати: темп, субтитри, довжина, що працює. Наприклад: «субтитри завжди, 20–35 с, демонстрація в перші 2 с».

## Платформи напряму
Де цей напрям заходить, з пріоритетом. Наприклад: «1) Instagram Reels, 2) TikTok».

## Чого уникати в цьому напрямі
Що не підходить саме тут, окремо від базового списку. Наприклад: «порівняння цін (швидко старіє), назви брендів у заголовку».
```

## Where it is written, saved and reused

- **Written:** `viral-scout` step 2 (the brief step of stage 0), into `<run>/direction-profile.md`, BEFORE the spend line of step 3 and before any paid call. The skill PROPOSES a filled profile from the topic and the base profile, shows it in full, and writes it only after the user confirms or corrects it.
- **Recorded:** `run.json.direction_profile` holds the slug of the direction (`null` when the run has none). See `run-layout.md`.
- **Saved:** after the user confirms it, the same text is also written to `library/profiles/<slug>.md` in the working folder (slug: lowercase ASCII with hyphens, from `Напрям`). `library/` is the user's private folder and is git-ignored.
- **Inferred, in a single-link audit run:** such a run names no topic, so `viral-breakdown` step 8 derives the direction profile from the breakdown files of that one video (`approved.md`, `analysis/01-marketing.md`, `analysis/01-motion.md`, `analysis/01-frames/watch-answer.md`) and writes it without asking. It is marked in `audit.md` as inferred from one video and not agreed with the user, so the user can correct the file. An existing `direction-profile.md` is never overwritten there.
- **Reused:** when a later run names a direction whose `library/profiles/<slug>.md` already exists, `viral-scout` step 2 offers that saved profile instead of inventing one: it shows it, the user confirms or edits it, and the result is copied into the run folder and written back to `library/profiles/<slug>.md`. A saved profile is never used without being shown.

## Search parameters

`descriptionLanguage` and `audienceQuery` are direction-specific and come from the direction profile, falling back to the base profile under the rule above. The exact mapping is in `source-queries.md`, section `Profile mapping`.
