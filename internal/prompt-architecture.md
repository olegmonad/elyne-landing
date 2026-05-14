# Elyne — Архитектура промтов и сфер

*Актуально на 14.05.2026. Источник: elyne.online/admin*

---

## Общая схема работы

```
Юзер проходит онбординг (вопросы 1-18+)
        ↓
profile_summary_system (ID 15) → строит Character Profile
        ↓
sphere_selector_prompt → выбирает ОДНУ из 9 активных сфер
        ↓
three_angles_prompt → строит 3 разных смысловых угла для сферы
        ↓
scene_system (ID 11) → генерирует сцены (текстовое описание)
        ↓
image_instructions (ID 12) → финальный промпт для AI-изображения
        ↓
FAL/SDXL → картинка
```

---

## Сферы (10 шт.)

| ID | Slug | Название | Близкие в кадре | В селекторе |
|----|------|----------|-----------------|-------------|
| 1 | self | Я и состояние | ❌ | ❌ исключена |
| 2 | resources | Ресурсы | ❌ | ✅ |
| 3 | realization | Реализация и влияние | ❌ | ✅ |
| 4 | love | Любовь и партнёрство | ✅ | ✅ |
| 5 | home | Дом, семья и близкие | ✅ | ✅ |
| 6 | children | Дети и наследие | ✅ | ✅ |
| 7 | creativity | Творчество и новые начинания | ❌ | ✅ |
| 8 | wisdom | Развитие и мудрость | ❌ | ✅ |
| 9 | freedom | Свобода и масштаб жизни | ❌ | ✅ |
| 10 | environment | Окружение | ❌ | ✅ |

**Сфера 1 (self) — исключена из автоселектора** (очевидно выбирается вручную или в отдельном флоу).

**Близкие в кадре** (show_relatives_in_three_angles = true): сферы 4, 5, 6 — любовь, дом, дети. Для них фото близких из профиля интегрируются в сцену (или силуэт/bokeh если фото нет).

---

## Стили одежды (10 стилей)

Одежда — один из ключевых рычагов персонализации. Юзер выбирает стиль в онбординге (Q18). Стиль подаётся в `{profile_summary}` и `three_angles_prompt`.

| ID | Slug | Название |
|----|------|----------|
| 13 | oldmoney | Old money |
| 14 | businessstyle | Business style |
| 15 | classic | Classic |
| 16 | casual | Casual |
| 17 | streetwear | Streetwear |
| 18 | sportcasual | Sport casual |
| 19 | boho | Boho |
| 20 | ytwok | Y2K |
| 21 | glam | Glam |
| 22 | romantic | Romantic |

**Как одежда влияет на генерацию:**
В `three_angles_prompt` есть правило: *«Одежда — соответствует {profile_summary} (Q18 / style-clotches). Один и тот же стиль адаптируется под характер каждого угла: домашний угол — расслабленная версия стиля, активный угол — собранная версия»*.

Т.е. стиль **не меняется** между углами, но адаптируется контекстуально. Для каждого стиля в базе хранятся отдельные `description_male` и `description_female` — текстовые описания гардероба, которые передаются в промпт как контекст.

---

## Промпты генерации (Промпты Генерации)

### ID 11 — scene_system (Основной промпт сцены)

**Назначение:** генерирует текстовые описания сцен (title + short_description + detailed_description в JSON).

**Ключевые принципы:**
- Emotionally believable life scenes — не реклама, не luxury catalog
- 6 Internal Validation Rules перед финальным ответом:
  1. Key Answer Locks — минимум 3 ключевых ответа юзера в сцене
  2. Identity Consistency — gender lock, age, personality core
  3. Real Life Feeling — не постановка, не influencer content
  4. Emotional Coherence — связь с Core Motives юзера
  5. Human Presence — действие + жизнь, не декоративный человек
  6. Anti-Stock Filter — без стоковых клише

### ID 15 — profile_summary_system (Профиль пользователя)

**Назначение:** строит Character Profile из ответов онбординга. Фиксирует «устойчивое ядро личности» которое сохраняется во всех сценах.

**Выходной формат:** текстовый профиль с:
- personality core
- gender lock
- age context
- environment type
- life level
- expression model
- emotional direction
- visual identity (включая стиль одежды из Q18)

### ID 12 — image_instructions (Инструкции для изображения)

**Назначение:** финальный блок для промпта AI-генерации. Visual Realism Rules.

**Что запрещено:**
- overly polished skin
- plastic beauty
- excessive glamour
- fashion-commercial look
- influencer aesthetics
- stock photo compositions

### ID 14 — relatives_instructions (Близкие в кадре)

**Назначение:** правила интеграции фото близких в сцену.

**Ключевое правило:** *«ВСЕ люди со ВСЕХ предоставленных изображений ДОЛЖНЫ появиться ВМЕСТЕ в финальном результате»* — сцена выглядит как подлинный спонтанный момент, не коллаж.

### ID 16 — affirmation (Аффирмация)

**Назначение:** текст после первой сцены. Закрепляет эмоциональное узнавание.

**Правила:** спокойная, человечная, grounded. НЕ мотивирует в лоб. Усиливает «ощущение возможности».

### ID 2-10, 32 — sphere-specific prompts

Отдельные промпты под каждую сферу (старая архитектура). Судя по наличию sphere_selector + three_angles в sphere-selector, они могут работать параллельно или быть legacy.

---

## Sphere Selector (отдельная страница)

**Два главных промпта:**

### sphere_selector_prompt
Диспетчер-промпт. Выбирает ОДНУ сферу на основе `{profile_summary}` + `{onboarding_answers}` путём сопоставления с `{spheres_catalog}`.

### three_angles_prompt
Режиссёр-промпт. Для выбранной сферы строит 3 принципиально разных смысловых окна (три угла). 

**Принцип трёх углов:**
- Угол 1: внутреннее, тихое, наедине с собой
- Угол 2: взаимодействие, контакт, признание
- Угол 3: действие, движение, реализация

**Для каждого угла определяется:** ключевое чувство → момент → локация → свет → план/ракурс → близкие в кадре → одежда.

**Входные переменные:**
- `{sphere_title}` / `{sphere_slug}`
- `{profile_summary}` — Character Profile юзера
- `{onboarding_answers}` — сырые ответы
- `{relatives_photos[]}` — фото близких
- `{sphere_definition}` — описание сферы из БД

---

## Активные вопросы онбординга

IDs: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 23

Q18 (style-clotches) — выбор стиля одежды — судя по всему обрабатывается отдельно (не в enabled_question_ids, но используется в profile_summary через `style-clotches`).

---

## Что передаётся в промпт при генерации сцены

```
Character Profile (из profile_summary_system):
  → personality core, gender, age, environment, life_level,
    expression_model, emotional_direction, visual_identity,
    style-clotches (Q18), KEY ANSWER LOCKS

Sphere Context:
  → sphere_title, sphere_slug, sphere_definition

Three Angles:
  → 3 смысловых окна с: feeling, moment, location, light, plan, clothing-adaptation

Relatives:
  → relatives_photos[] (для сфер 4/5/6) + relatives_instructions

Image Rules:
  → image_instructions (visual realism rules)
```

---

*Данные извлечены из elyne.online/admin 2026-05-14*
