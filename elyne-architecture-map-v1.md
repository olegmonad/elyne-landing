# Elyne — Architecture Map системы генерации

> Подготовлено для промт-инженера. Основа — актуальный бэкап базы `backup_nextme_20260421`.
> Дата: 2026-05-13.

---

## ЧТО ВВОДИТ ПОЛЬЗОВАТЕЛЬ (raw truth)

---

# SECTION: onboarding

## Q1 — Что для тебя сейчас важно?
- type: multi-select (max 3, prioritized)
- used_in: stage_1 (онбординг)
- read_by: llm (profile_summary_system)
- example: ["Быть признанным и увиденным", "Влиять и быть значимым", "Выглядеть и ощущаться как лучшая версия себя"]
- required: yes
- affects:
  - profile.core_motives
  - profile.key_answer_locks
  - сцена: что человек ищет в кадре (признание / влияние / образ)

## Q2 — На какой уровень жизни ты хочешь выйти?
- type: single-select
- used_in: stage_1
- read_by: llm (profile_summary_system)
- example: "Высокий уровень жизни"
- required: yes
- options: Спокойная и комфортная / Стабильный рост / Новые возможности / Высокий уровень / Влияние и большие проекты
- affects:
  - profile.life_level
  - масштаб и статус сцены

## Q3 — В какой среде ты видишь свою жизнь?
- type: single-select
- used_in: stage_1
- read_by: llm (profile_summary_system)
- example: "Жизнь у моря"
- required: yes
- options: Мегаполис / Тихий город или пригород / Природа / Жизнь у моря / Свободная жизнь в разных странах
- affects:
  - profile.environment_type
  - фон и архитектура сцены

## Q5 — В чём ты хочешь реализовываться?
- type: multi-select (max 2)
- used_in: stage_1
- read_by: llm (profile_summary_system)
- example: ["Собственное дело", "Творчество и личные проекты"]
- required: yes
- affects:
  - profile.realization_domain
  - тип активности в сцене

## Q6 — На каком уровне ты хочешь проявлять себя?
- type: single-select
- used_in: stage_1
- read_by: llm (profile_summary_system)
- example: "На широком уровне и с большим влиянием"
- required: yes
- affects:
  - profile.life_level (дополнительный вес)
  - количество людей вокруг / социальный контекст сцены

## Q7–Q12 — Стиль (binary-выбор, 6 пар)
- type: binary (6 раундов, каждый = выбор одного из 2)
- used_in: stage_1
- read_by: llm (через profile_summary → visual_identity_ranked)
- example: Q7: "Классический", Q8: "Минималистичный", Q10: "Современный городской"
- required: yes
- affects:
  - profile.visual_identity_ranked
  - clothing style в сцене (прямая привязка slug → clothing description)

## Q14 — Через что тебе нравится проявляться?
- type: multi-select (max 3, prioritized)
- used_in: stage_1
- read_by: llm (profile_summary_system)
- example: ["через образ и внешний вид", "через стиль жизни", "через влияние на других"]
- required: yes
- affects:
  - profile.expression_model
  - как именно человек «действует» в сцене

## Q15 — Что должно ощущаться первым, когда люди видят твою жизнь?
- type: multi-select (max 3, prioritized)
- used_in: stage_1
- read_by: llm (profile_summary_system)
- example: ["вау", "стиль", "свобода"]
- required: yes
- affects:
  - profile.social_signal
  - атмосфера и тон сцены

## Q16 — Что для тебя важнее в результате?
- type: single-select
- used_in: stage_1
- read_by: llm (meta_prompt при генерации сцены)
- example: "чтобы это была моя более сильная версия"
- required: yes
- affects:
  - profile.generation_mode
  - уровень идеализации vs реализма в сцене

## Q17 — Что ты хочешь усилить в своей жизни?
- type: single-select
- used_in: stage_1
- read_by: llm (meta_prompt при генерации сцены)
- example: "деньги"
- required: yes
- affects:
  - profile.enhancement_focus
  - контекст атрибутов в сцене

## Q18 — Какой образ тебе ближе всего?
- type: single-select (8 вариантов)
- used_in: stage_1
- read_by: llm
- example: "яркий и притягательный"
- required: yes
- affects:
  - profile.visual_identity_ranked (перекрывает Q7-Q12 при конфликте)
  - стиль одежды и подача образа

## user_photo
- type: image (jpeg/png)
- used_in: stage_1 → stage_2
- read_by: fal (image-to-image)
- example: фото лица пользователя
- required: yes
- affects:
  - facial identity preservation в сцене
  - gender detection (косвенно)

---

# SECTION: sphere_questions

> Каждая из 10 сфер задаётся после онбординга, при первом входе в сферу.
> Q1 = рамочный вопрос (что в этой сфере сейчас), Q2 = уточнение, Q3 = повторяется при каждой генерации сцены.

## sphere_q1
- type: open-text или single-select (зависит от сферы)
- used_in: stage_2 (при генерации сцены сферы)
- read_by: llm (sphere meta_prompt)
- example: "Хочу выйти на мировой уровень в своей нише"
- required: yes (при первом входе в сферу)
- affects:
  - контекст и цель сцены для этой сферы

## sphere_q2
- type: open-text или select
- used_in: stage_2
- read_by: llm
- example: "Через публичное присутствие и личный бренд"
- required: yes (при первом входе)
- affects:
  - способ реализации в сцене

## sphere_q3
- type: open-text (каждый раз при генерации)
- used_in: stage_2
- read_by: llm
- example: "Хочу сцену, где я выступаю перед большой аудиторией"
- required: yes
- affects:
  - конкретный сценарий текущей генерации

---

## ЧТО ГЕНЕРИРУЕТ AI (derived entities)

---

# SECTION: profile

## profile_summary (Character Profile)
- type: text (структурированный, ~300-500 слов)
- used_in: stage_2 (каждая генерация сцены)
- read_by: llm (все meta_prompt'ы stage_2)
- generated_by: llm (type=profile_summary_system)
- source: onboarding_answers (Q1-Q18)
- required: yes
- affects:
  - identity consistency между всеми сценами
  - gender lock, visual identity, environment, life level
- format (строгий):
  ```
  Character Profile:

  Gender: male / female
  Age Context: ...
  Archetype: ...
  Core Motives: ...
  Expression Model: ...
  Visual Identity: ...
  Social Signal: ...
  Life Level: ...
  Environment Type: ...
  Realization Path: ...
  Realization Domain: ...
  Energy Type: ...
  Key Answer Locks:
  - ...
  - ...
  - ...
  ```
- note: Key Answer Locks — блок ответов, которые ОБЯЗАНЫ проявиться в каждой сцене. Если сцена не содержит хотя бы 3 из них — сцена невалидна.

## scene_title
- type: text (2–5 слов)
- used_in: UI (карточка сцены)
- read_by: пользователь
- generated_by: llm (type=profile_photo / field_scene → title_meta_prompt)
- source: profile_summary + onboarding_answers + scene_description
- required: yes
- affects:
  - первое впечатление пользователя от сцены

## scene_description (short_description)
- type: text (1–2 предложения)
- used_in: UI (подпись под сценой)
- read_by: пользователь
- generated_by: llm (type=scene_system)
- required: yes
- affects: не влияет на FAL

## detailed_description
- type: text (~200-400 слов, кино-описание)
- used_in: stage_2 (передаётся в image_prompt pipeline)
- read_by: llm (финальный image-промпт builder) → fal
- generated_by: llm (type=scene_system)
- required: yes
- affects:
  - основной контент FAL-промпта
  - всё что будет на изображении

---

## ЧТО РЕДАКТИРУЕТСЯ ВРУЧНУЮ (manual override)

---

# SECTION: generation_prompts (admin-editable)

> 16 записей в таблице. Администратор правит через CMS. Изменения применяются ко ВСЕМ новым генерациям немедленно.

## meta_prompt
- type: text (большой промпт, 200-900 слов)
- used_in: stage_2
- read_by: llm (OpenRouter)
- edited_by: admin (ручной override)
- required: yes
- risk: **manual override ломает coherence** — если мета-промпт противоречит profile_summary или Key Answer Locks, система начинает давать сцены не в интересах пользователя
- affects:
  - логика интерпретации ответов
  - правила валидации сцены (DEBUG CHECK)
  - ограничения (anti-pattern, gender lock, realization lock)
- types (16 промтов):
  - `profile_photo` — первая сцена (самая важная)
  - `field_scene` (×10, по одному на сферу)
  - `scene_system` — system prompt для JSON-генерации вариантов
  - `image_instructions` — инструкции для FAL
  - `variation_instructions` — вариация существующей сцены
  - `relatives_instructions` — интеграция близких
  - `profile_summary_system` — генерация Character Profile
  - `affirmation` — аффирмация после первой сцены

## title_meta_prompt
- type: text
- used_in: profile_photo только
- read_by: llm
- edited_by: admin
- required: yes (только для profile_photo)
- affects:
  - название первой персональной сцены

## image_suffix
- type: text (хвост image-промпта, 2-5 предложений)
- used_in: FAL
- read_by: fal
- edited_by: admin
- required: yes
- affects:
  - финальный хвост всех FAL-промптов
  - facial identity preservation instructions
  - технические параметры (план, стиль)

---

## ГДЕ НАЧИНАЕТСЯ FAL

---

# SECTION: image_generation

## fal_prompt (финальный)
- type: text (собирается из нескольких частей)
- used_in: FAL API
- read_by: fal image model
- generated_by: llm (финальный builder) + admin (image_suffix)
- structure:
  ```
  [detailed_description]
  +
  [image_instructions meta_prompt]
  +
  [image_suffix]
  ```
- required: yes
- affects:
  - всё что на изображении

## fal_input_image
- type: image (user_photo)
- used_in: FAL (image-to-image / face swap)
- read_by: fal
- required: yes
- affects:
  - facial identity в результате

---

## ЧТО ХРАНИТСЯ МЕЖДУ ГЕНЕРАЦИЯМИ

---

# SECTION: persistence

## profile_summary (persistent)
- хранится: после онбординга, переиспользуется в каждой генерации
- affects: все сцены для данного пользователя

## sphere_answers (Q1+Q2, persistent)
- хранится: после первого входа в сферу
- affects: все последующие генерации в этой сфере (Q3 новый каждый раз)

## previous_scenes
- хранится: **НЕТ в текущей реализации**
- visual continuity, clothing continuity, emotional continuity между сценами — **отсутствуют**
- note: это архитектурная дыра — если пользователь генерирует 2 сцены в разных сферах, система не знает о первой при генерации второй

## user_photo (persistent)
- хранится: после photo-upload
- affects: все генерации пользователя

---

## ПОЛНЫЙ PIPELINE (один реальный кейс)

```
onboarding_answers (Q1/Q3/Q5/Q6/Q14/Q15/Q16/Q17/Q18 + binary Q7-Q12)
↓
[LLM: type=profile_summary_system]
Промпт: "Ты создаёшь Character Profile пользователя на основе его ответов..."
Вход: {onboarding_answers}
Выход: Character Profile (Gender / Age Context / Archetype / Core Motives / Key Answer Locks / ...)
↓
profile_summary хранится в БД
↓
Пользователь выбирает сферу → отвечает на sphere_q1 + sphere_q2
↓
[LLM: type=scene_system]
System prompt: "Сгенерируй {count} вариантов сцены. Ответь строго в формате JSON: [{"title":"...","short_description":"...","detailed_description":"..."}]"
User prompt: [meta_prompt сферы] + {profile_summary} + {onboarding_answers} + {sphere_q1} + {sphere_q2} + {sphere_q3}
Выход: JSON массив вариантов сцен
↓
Пользователь выбирает сцену (или система берёт первую)
↓
detailed_description → [LLM: image prompt builder]
Вход: detailed_description + image_instructions + image_suffix
Выход: финальный FAL-промпт (чистый текст)
↓
[FAL API: image-to-image]
Вход: fal_prompt + user_photo
Выход: result image
↓
[LLM: title_meta_prompt] (только для profile_photo)
Вход: profile_summary + onboarding_answers + scene_description
Выход: scene_title (2–5 слов)
```

---

## JSON SCHEMA ОТВЕТА LLM (scene_system)

```json
[
  {
    "title": "Свободная жизнь у моря",
    "short_description": "Утро на террасе с видом на океан. Ты дома — в самом точном смысле этого слова.",
    "detailed_description": "Мужчина 35-40 лет стоит у открытой террасы с видом на Средиземное море. Рано утро, мягкий золотой свет. Лёгкая льняная рубашка. Кофе в руке, взгляд в сторону горизонта. Ощущение — человек, который заслужил это место. Не турист. Живёт здесь. Позади — просторная комната с натуральными материалами. Впереди — тихий, масштабный, очень личный момент."
  }
]
```

---

## КАК РАБОТАЕТ SPHERE SYSTEM

Сфера — это **emotional lens** (линза восприятия жизни) + **narrative category** (категория сцены).

Не просто тема и не стиль жизни.

Каждая сфера:
- имеет slug (состояние / ресурсы / реализация / партнёрство / дом / род / творение / развитие / свобода / окружение)
- содержит definition (что эта сфера означает в контексте Elyne)
- запускает свой field_scene meta_prompt (специфичный для данной сферы язык)
- имеет Q1/Q2 (задаются один раз при первом входе) + Q3 (каждая генерация)

Sphere НЕ является:
- тегом стиля жизни
- классификатором ценностей
- HR-анкетой

Sphere — это угол, через который пользователь смотрит на желаемую жизнь прямо сейчас. Один человек может иметь активные сцены в нескольких сферах, и они не конфликтуют между собой в UI.

Текущая проблема: **сферы изолированы** — метапромпт «Реализация» не знает о предыдущей сцене «Свобода» того же пользователя. Continuity между сферами нет.

---

## ЧТО ОТСУТСТВУЕТ (архитектурные дыры)

1. **Continuity между генерациями** — clothing/visual/emotional continuity не передаётся между сценами
2. **Validator** — нет автоматической проверки что Key Answer Locks проявились в сцене (DEBUG CHECK прописан в мета-промпте, но нет внешнего валидатора)
3. **Retry logic** — если сцена невалидна, нет автоматического пересбора
4. **Sphere cross-awareness** — сфера не знает о других сферах пользователя
5. **JSON schema enforcement** — system prompt говорит «только JSON», но нет schema validation на уровне кода (по крайней мере не видно в дампе)
6. **Emotional interpreter** — между onboarding_answers и meta_prompt нет отдельного слоя интерпретации эмоционального состояния пользователя прямо сейчас

---

*Файл подготовлен из: `admin-content-dump_v1.md` (7801 строк) + `elyne-prompt-engineering-v1.md` (9270 строк)*
