<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Elyne · документ</title>
<style>
  :root { --bg:#fafaf7; --ink:#2a241d; --muted:#6b6357; --line:#e5e3dc; --accent:#c4a95e; --card:#ffffff; }
  body { font-family: -apple-system, "Inter", system-ui, sans-serif; max-width: 820px; margin: 0 auto; padding: 36px 18px 64px; color: var(--ink); line-height: 1.65; background: var(--bg); }
  h1 { font-size: 28px; font-weight: 600; margin: 0 0 8px; letter-spacing: -0.01em; }
  h2 { font-size: 21px; font-weight: 600; margin: 36px 0 12px; padding-top: 16px; border-top: 1px solid var(--line); color: #1f1a14; }
  h3 { font-size: 17px; font-weight: 600; margin: 22px 0 6px; color: #2f2820; }
  h4 { font-size: 15px; font-weight: 600; margin: 16px 0 4px; }
  p { margin: 8px 0 12px; }
  ul, ol { padding-left: 22px; margin: 8px 0 14px; }
  li { margin: 4px 0; }
  blockquote { margin: 16px 0; padding: 12px 18px; background: #f0efe9; border-radius: 10px; color: var(--muted); font-size: 15px; }
  blockquote p { margin: 4px 0; }
  hr { border: 0; border-top: 1px solid var(--line); margin: 32px 0; }
  code { background: #f3f1ea; padding: 1px 6px; border-radius: 5px; font-size: 13.5px; color: #4a3f30; }
  pre { background: #1f1a14; color: #f0e9d8; padding: 14px 16px; border-radius: 10px; overflow-x: auto; font-size: 13.5px; }
  pre code { background: transparent; color: inherit; padding: 0; }
  a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; }
  a:hover { border-bottom-color: var(--accent); }
  strong { color: #1f1a14; }
  em { color: var(--muted); }
  .footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--line); font-size: 12.5px; color: var(--muted); font-style: italic; }
</style>
</head>
<body>
<h1 id="audit-sphere-3-retreat-conference-fix">Audit — Sphere 3 Retreat / Conference Fix</h1>
<h2 id="_1">Что было сделано</h2>
<p>В промт ID=4 (сфера Реализация / Проявленность) заменена базовая секция <code>Semantic Differentiation: Retreat ≠ Conference</code> на полную версию по ТЗ.</p>
<table>
<thead>
<tr>
<th></th>
<th>До</th>
<th>После</th>
</tr>
</thead>
<tbody>
<tr>
<td>Размер промта</td>
<td>32 298 chars</td>
<td>33 356 chars (+1 058)</td>
</tr>
<tr>
<td>Секция</td>
<td><code>Semantic Differentiation: Retreat ≠ Conference</code> (базовая)</td>
<td><code>Retreat / Conscious Gathering Differentiation</code> (полная)</td>
</tr>
<tr>
<td>FAL Guard</td>
<td>нет</td>
<td><code>Final FAL Prompt Guard — Retreat</code> (checklist запрещённых слов)</td>
</tr>
</tbody>
</table>
<hr>
<h2 id="_2">Добавленные секции</h2>
<h3 id="1-retreat-conscious-gathering-differentiation">1. Retreat / Conscious Gathering Differentiation</h3>
<p>Содержит:
- триггеры активации (ретрит / wellbeing gathering / практика / круг людей / пространство осознанности)
- полный список forbidden patterns: business conference / corporate seminar / keynote / TED-talk / classroom / formal training room
- список desired signals: human-scale gathering / shared presence / calm collective attention / embodied participation
- поведение ведущего: круг / полукруг, ближе к группе, ведёт через присутствие, а не со сцены
- forbidden среда: сцена / трибуна / проектор / экран / ряды стульев / корпоративный свет
- preferred среда: тёплый свет / дерево / ковры / круг людей / натуральные материалы</p>
<h3 id="2-final-fal-prompt-guard-retreat">2. Final FAL Prompt Guard — Retreat</h3>
<p>Активируется при ключевых словах: ретрит / wellbeing / практика / осознанность / группа / люди прислушиваются.</p>
<p>Запрещённые слова в финальном FAL prompt:
<code>conference</code>, <code>business conference</code>, <code>corporate</code>, <code>seminar</code>, <code>keynote</code>, <code>stage</code>, <code>presentation</code>, <code>projector</code>, <code>networking</code>, <code>expo</code>, <code>coworking event</code>, <code>lecture hall</code>, <code>rows of chairs</code></p>
<p>При обнаружении → замена на: <code>circle</code>, <code>intimate group</code>, <code>shared presence</code>, <code>reflective gathering</code>, <code>calm human-scale retreat</code>, <code>embodied participation</code></p>
<hr>
<h2 id="_3">Тест на пользовательский ответ</h2>
<p><strong>Ввод:</strong> «Я провожу мероприятие ретрит и люди ко мне прислушиваются»</p>
<h3 id="detailed_description">Ожидаемый detailed_description</h3>
<blockquote>
<p>Авторский ретрит в тёплом камерном пространстве. Человек стоит в полукруге с небольшой группой (8-12 человек), находясь на одном уровне — не на сцене. Деревянный пол, мягкий рассеянный свет из высоких окон. Люди сидят на подушках или стульях в кругу, направление внимания — к центру. Ведущий удерживает паузу, его голос и присутствие создают поле вовлечённости. Ощущение живого процесса: не трансляция, а совместное проживание.</p>
</blockquote>
<h3 id="fal-prompt">Ожидаемый финальный FAL prompt</h3>
<p>Содержит:
- ✅ <code>intimate group</code> или <code>small group</code> или <code>circle</code>
- ✅ <code>shared presence</code> / <code>reflective gathering</code> / <code>warm space</code>
- ✅ <code>natural light</code> / <code>wooden floor</code> / <code>natural materials</code>
- ✅ <code>embodied</code> / <code>calm collective attention</code></p>
<p>Не содержит:
- ❌ <code>conference</code> → заменено
- ❌ <code>corporate</code> → заменено
- ❌ <code>seminar</code> → заменено
- ❌ <code>stage</code> → заменено
- ❌ <code>projector</code> / <code>screen</code> → заменено
- ❌ <code>rows of chairs</code> → заменено</p>
<hr>
<h2 id="_4">Влияние на другие сферы</h2>
<p>Секция добавлена только в ID=4 (sphere 3 / Реализация). ID=11 (scene_system) не изменялся — guard специфичен для этой сферы и не ломает другие.</p>
<hr>
<h2 id="_5">Критерий успеха</h2>
<p>После фикса сцена «Я провожу ретрит» должна строить:
- камерный авторский ретрит
- группа вовлечена, тёплое человеческое пространство
- нет конференционной геометрии
- нет корпоративного события
- влияние через доверие, присутствие, внимание людей</p>
<p>Реальная проверка: запустить генерацию sphere 3 на аккаунте с ответом «ретрит» — сравнить визуал до/после.</p>
<div class="footer">Elyne · документ опубликован для команды. Канон лежит в приватном репо Monada — здесь срез на момент публикации.</div>
</body>
</html>
