# Elyne — Ответы на вопросы промт-инженера по `{chosen_clothing_style}`

**Дата:** 2026-05-14  
**Источник:** Прямая инспекция admin.elyne.online (production DB, реальные пользовательские данные)

---

## Q1: В каком формате `{chosen_clothing_style}` попадает в промт?

**Ответ: Полный структурированный текст описания стиля** (не slug, не title, не JSON).

### Точный формат (из реального промта, пользователь с Streetwear)

Когда у пользователя выбран один стиль, в поле `{chosen_clothing_style}` (field_scene prompt, IDs 2–10, 32) подставляется:

```
СТИЛИ ОДЕЖДЫ:
- Streetwear: Visual Code: уличный fashion-forward, не массовый hip-hop. Точный крой при оверсайзе. Base Wardrobe: - Верх: премиум-худи, графический long-sleeve, оверсайз-рубашка. - Низ: прямые / широкие брюки, премиум-деним, карго. - Обувь: массивные lifestyle-кроссовки (не беговые). - Верхняя одежда: анорак, оверсайз-куртка, бомбер. - Аксессуары: crossbody, beanie, кепка. Materials: ripstop, нейлон, плотный premium-хлопок, деним, технический трикотаж. Color Logic: графит, хаки, приглушённый вишнёвый, выцветший индиго. Бренд-акцент — редко и точечно. Social Signal: креативность, fashion-литература, городская независимость. Best Scene Fit: Творчество · Реализация · Свобода · Окружение · Состояние. Avoid: total-look бренда, sportswear, fast-fashion подделки, sneakerhead-нагромождение.
```

### Источник этого текста

Поле `description_male` (или `description_female` — по полу пользователя) из таблицы `clothing_styles` в БД.

В таблице хранятся: `id`, `slug`, `name`, `description_male`, `description_female`, `image_url_male`, `image_url_female`.

Пример записи:
- `slug = streetwear`
- `name = Streetwear`
- `description_male = [полный текст выше]`

При подстановке backend берёт нужное поле по полу пользователя и вставляет **без изменений** (raw text).

### Тот же текст в profile_summary_system

Аналогичный блок приходит в `profile_summary_system` (ID 15) как:

```
Выбранные стили одежды: СТИЛИ ОДЕЖДЫ:
- Streetwear: Visual Code: ... Base Wardrobe: ...
```

→ AI синтезирует из него `Visual Identity` в character profile → этот profile через `{profile_summary}` попадает в `three_angles_prompt`.

**Итог по Q1**: Это **merged text** из DB-поля — полная структурированная карточка стиля, не slug, не JSON, не только title.

---

## Q2: Где хранится style selection logic?

**Ответ: Двухуровневая структура. НЕ в `onboarding_answers`.**

### Уровень 1 — Онбординг (что пользователь выбрал)

- Таблица: `user_clothing_styles` (pivot: user_id → clothing_style_id)
- Создаётся на странице онбординга slug=`style-clotches` (questionnaire_id=18, type=profile)
- Хранит список стилей которые выбрал пользователь (может быть несколько)

### Уровень 2 — Резолюция per-sphere (что реально используется)

Видно в admin-панели (вкладка "Выбранные стили одежды" на пользователе):

| Card | Сфера | Статус | Стиль | Обоснование |
|------|-------|--------|-------|-------------|
| 5902 | Любовь и партнёрство | Готово | Streetwear | auto-selected: только один стиль выбран пользователем |
| 5902 | Реализация и влияние | Готово | Streetwear | auto-selected: только один стиль выбран пользователем |
| 5902 | Свобода и масштаб жизни | Готово | Streetwear | auto-selected: только один стиль выбран пользователем |

Это значит:
- Перед генерацией сцены backend **резолвит** какой стиль использовать для этой сферы
- Если пользователь выбрал один стиль → auto-selected
- Если несколько → есть logic выбора (предположительно по Best Scene Fit из description)
- Результат записывается в отдельную таблицу (что-то вроде `card_visual_identities` / `chosen_styles`)

### Схема потока данных

```
ОНБОРДИНГ
  ↓
user_clothing_styles (pivot: user ↔ clothing_styles)
  ↓
Триггер генерации для сферы X
  ↓
Resolve: какой стиль для этой сферы?  ← ЛОГИКА ВЫБОРА ЗДЕСЬ
  ↓
Записать в card_visual_identities (card_id, sphere, chosen_style_slug)
  ↓
Fetch description_male/female из clothing_styles
  ↓
Подставить в {chosen_clothing_style} в field_scene prompt
  ↓
AI генерирует scene description
  ↓
FAL получает финальный image prompt
```

---

## Вывод для архитектуры interpretation layer

### Можно ли добавить без рефакторинга backend?

**Да, но нужен промежуточный synthesis step** между точкой 4 и 5 в схеме выше.

**Текущее состояние:**  
`chosen_style_slug` → `description_text` (raw) → `{chosen_clothing_style}` в field_scene

**С interpretation layer:**  
`chosen_style_slug` + `user_profile_summary` → LLM synthesis → `contextualized_style_description` → `{chosen_clothing_style}`

Это НЕ требует рефакторинга `onboarding_answers` или `user_clothing_styles`.  
Требует: хука в backend между резолюцией стиля и подстановкой в промт.

### Что уже есть «бесплатно»

`profile_summary_system` (ID 15) уже делает частичный синтез:  
`answers + style_description` → `Visual Identity` в character profile  
→ этот профиль через `{profile_summary}` попадает в `three_angles_prompt`

То есть для пути через three_angles → field_scene, интерпретация **уже происходит** косвенно через profile.

**Точка наибольшего влияния** для нового interpretation layer — это блок `field_scene` (IDs 2–10), где `{chosen_clothing_style}` подставляется напрямую из DB без дополнительного синтеза.

---

## Доп. данные по структуре промтов

| ID | Тип | Где используется `{chosen_clothing_style}` |
|----|-----|-------------------------------------------|
| 2–10 | `field_scene` | Прямо в секции "Выбранный стиль одежды:" |
| 32 | `field_scene` | (альтернативный field_scene) |
| 15 | `profile_summary_system` | Через "Выбранные стили одежды:" в input |
| 11, 12 | `scene_system`, `image_instructions` | Нет, стиль приходит из profile_summary |
| 14, 16, 19 | `relatives_instructions`, `affirmation`, `scene_affirmation` | Не используется |

---

*Документ создан на основе прямой инспекции production admin panel elyne.online. Все данные актуальны на 2026-05-14.*
