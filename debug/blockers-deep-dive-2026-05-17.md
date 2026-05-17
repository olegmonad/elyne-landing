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
<h1 id="3-p0-">Глубокий разбор 3 P0-блокеров</h1>
<blockquote>
<p>Paywall 0₽ × 3 берёт Денис в понедельник — здесь его не разбираем.
Эти три бага требуют решения <strong>до</strong> того, как идём фиксить, потому что у двух из них лечение задевает архитектуру pipeline.</p>
</blockquote>
<hr>
<h2 id="b2-profile-error-visual_identity">B2. Profile ERROR при синтезе visual_identity</h2>
<h3 id="_1">Краткая суть</h3>
<p>Юзер выбрал в онбординге 3 стиля одежды: <strong>Casual + Classic + Boho</strong>. Pipeline <code>profile_summary</code> (OpenRouter) не смог собрать из них <strong>одну</strong> visual_identity без нарушения принципа <strong>No.Synthetic.Personality</strong> — вернул ERROR. Каскадом ломается всё: clothing continuity, character spine, identity drift.</p>
<h3 id="5">По 5 осям</h3>
<table>
<thead>
<tr>
<th>Ось</th>
<th>Диагноз</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Где ломается</strong></td>
<td>Этап синтеза <code>profile_summary</code> в OpenRouter pipeline (до FAL). Метапромпт пытается выдать валидный JSON-профиль из 3 разнонаправленных стилей.</td>
</tr>
<tr>
<td><strong>Слой</strong></td>
<td><strong>Prompt-layer</strong>. Constraint «No.Synthetic.Personality» формулирован так, что 3 разных стиля = «синтетическая личность» → AI отказывается синтезировать → ERROR.</td>
</tr>
<tr>
<td><strong>FAL или routing</strong></td>
<td>Ни то, ни другое. FAL на этом этапе ещё не вызывается. Это <strong>prompt-design issue</strong> в OpenRouter-стороне.</td>
</tr>
<tr>
<td><strong>Воспроизводимость</strong></td>
<td><strong>100%</strong> при любом выборе ≥ 2 разных стилей. Тест-акк monad@elyne.online воспроизвёл с первого захода.</td>
</tr>
<tr>
<td><strong>Scope</strong></td>
<td><strong>Все юзеры с multi-style выбором</strong> (а это большинство — Casual/Classic/Boho/Sport/Bohochic — это нормальные комбинации). При ERROR: clothing default per-sphere → разные стили в разных сферах → identity drift.</td>
</tr>
</tbody>
</table>
<h3 id="_2">Корень проблемы</h3>
<p>Сейчас <code>profile_summary</code> устроен как <strong>all-or-nothing</strong>: либо валидный JSON, либо ERROR + raw onboarding передаётся метапромпту как fallback. <strong>Fallback не работает корректно</strong>, потому что метапромпт «первой сцены» берёт <strong>sphere-default clothing</strong>, а не raw user styles.</p>
<h3 id="_3">Варианты фикса (от мягкого к жёсткому)</h3>
<ol>
<li><strong>Soft fix (1-2 часа)</strong> — расширить prompt-инструкцию <code>profile_summary</code>: «multiple styles ≠ synthetic personality, выбирай dominant style + 1 accent». <strong>Риск:</strong> AI сам решит что dominant — может промахнуться.</li>
<li><strong>Mid fix (полдня)</strong> — добавить <strong>composite style logic</strong>: если выбрано ≥ 2 стилей → не синтезируем в одну identity, а строим <strong>per-occasion mapping</strong> (work=Classic, leisure=Casual, ceremonial=Boho). Метапромпт сцены выбирает по контексту сферы.</li>
<li><strong>Hard fix (день)</strong> — отказаться от синтеза в текст-описание, передавать в метапромпт <strong>structured visual_identity object</strong>: <code>{styles: [...], colors: [...], silhouettes: [...]}</code>. Метапромпт сам комбинирует по контексту.</li>
</ol>
<h3 id="_4">Моя рекомендация</h3>
<p><strong>Mid fix (2)</strong>. Soft слишком хрупкий (AI промахнётся на 30-40% акков), hard — переделка контракта <code>profile_summary</code> → задевает Дениса. Mid решает 90% случаев и не ломает API.</p>
<h3 id="_5">Что нужно от тебя для постановки</h3>
<ul>
<li>Утвердить вариант фикса (1/2/3)</li>
<li>Решить: при per-occasion mapping — кто решает что «work» а что «leisure» для каждой сферы? Hardcode таблица 10 сфер × occasion-тип, или AI определяет на месте?</li>
</ul>
<hr>
<h2 id="b3-wish-iterations-bypass-prompt-engine">B3. Wish-iterations bypass prompt-engine</h2>
<h3 id="_6">Краткая суть</h3>
<p>Когда юзер пишет уточнение к сцене («Я иду кору», «Я иду у кайласа»), pipeline шлёт в FAL <strong>только текст пожелания + tech rules</strong>. OpenRouter (метапромпт сцены) <strong>не вызывается</strong>. FAL получает голый wish без mise-en-scène, camera angle, atmospheric direction → результат непредсказуем.</p>
<h3 id="5_1">По 5 осям</h3>
<table>
<thead>
<tr>
<th>Ось</th>
<th>Диагноз</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Где ломается</strong></td>
<td>На уровне <strong>роутинга wish-флоу</strong> в orchestration. Условие <code>if source = previous_generation AND user_comment != null</code> направляет в shortcut-ветку, минуя scene-generation.</td>
</tr>
<tr>
<td><strong>Слой</strong></td>
<td><strong>Orchestration-layer</strong>. Промты в порядке — их просто не зовут.</td>
</tr>
<tr>
<td><strong>FAL или routing</strong></td>
<td><strong>Routing</strong>. FAL делает что может с тем что прислали (а прислали 5 слов и tech rules).</td>
</tr>
<tr>
<td><strong>Воспроизводимость</strong></td>
<td><strong>100%</strong> на любом wish-комментарии. Видно на #593 («Я иду кору») и #594 («Я иду у кайласа») — оба плоские.</td>
</tr>
<tr>
<td><strong>Scope</strong></td>
<td><strong>Все wish-итерации</strong> во всех сферах. Это feature итерационного флоу — её ломает каждый юзер, который добавляет комментарий.</td>
</tr>
</tbody>
</table>
<h3 id="_7">Корень проблемы</h3>
<p>Архитектурное решение «wish = быстрая итерация без переразбора» было оправдано как оптимизация (меньше OpenRouter-вызовов). На практике оптимизация даёт <strong>систематически плохой cinematic</strong> — экономим 2-3 секунды и теряем качество главного use-case (юзер уточняет = вкладывается = ждёт лучшего результата).</p>
<h3 id="_8">Варианты фикса</h3>
<ol>
<li><strong>Wish-wrapper (полдня)</strong> — добавить middleware: <code>wish → mini-scene-generation (OpenRouter) → FAL</code>. Метапромпт получает previous_prompt + wish → строит enriched scene description с сохранённой композицией. <strong>Cost:</strong> +1 OpenRouter call на wish-итерацию (~$0.001).</li>
<li><strong>Wish-merge (час)</strong> — взять previous_prompt и подставить wish в раздел «action/motion» через regex/template. Не зовём OpenRouter вообще. <strong>Риск:</strong> не учитывает radical wish-shift («я иду» vs «я лежу»).</li>
<li><strong>Hybrid</strong> — wish классифицируется (мелкий refinement / radical shift). Refinement → wish-merge (быстро), shift → wish-wrapper (полная переработка).</li>
</ol>
<h3 id="_9">Моя рекомендация</h3>
<p><strong>Wish-wrapper (1)</strong>. Это правильный архитектурный фикс, +$0.001/итерация — копейки относительно качества. Hybrid красив, но requires classifier — лишняя сложность для MVP.</p>
<h3 id="_10">Что нужно от тебя</h3>
<ul>
<li>Утвердить wish-wrapper</li>
<li>Решить: показывать ли юзеру индикатор «обрабатываю уточнение…» (на 1-2 секунды дольше станет)</li>
</ul>
<hr>
<h2 id="b4-sphere-3-retreat-conference-hall-mismatch">B4. Sphere 3: retreat → conference hall mismatch</h2>
<h3 id="_11">Краткая суть</h3>
<p>Промт сферы 3 («Реализация») генерирует «авторский ретрит» (корректно). FAL.ai интерпретирует визуальную композицию «лофт + аппаратура + аудитория за дверью» <strong>как конференц-зал</strong> — это bias обучающей выборки FAL (&ldquo;loft + audio gear + audience&rdquo; → corporate event).</p>
<h3 id="5_2">По 5 осям</h3>
<table>
<thead>
<tr>
<th>Ось</th>
<th>Диагноз</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Где ломается</strong></td>
<td>На <strong>рендеринге FAL</strong>. Сам промт в #604 корректный: «авторский ретрит», «интимная атмосфера».</td>
</tr>
<tr>
<td><strong>Слой</strong></td>
<td><strong>FAL training bias</strong> — модель ассоциирует визуальные элементы с corporate event. Prompt-layer не виноват, но может <strong>компенсировать</strong> через negative prompt.</td>
</tr>
<tr>
<td><strong>FAL или routing</strong></td>
<td><strong>FAL</strong> (визуальный bias модели).</td>
</tr>
<tr>
<td><strong>Воспроизводимость</strong></td>
<td>Стабильно когда промт сферы 3 содержит «лофт / зал / аппаратура / аудитория». Если промт уводит в «природа / open air / круг людей сидя» — bias не срабатывает.</td>
</tr>
<tr>
<td><strong>Scope</strong></td>
<td>Sphere 3 («Реализация»). Потенциально может бить любую сферу, где сцена включает «event с аудиторией» (свадьба? презентация книги?). Сейчас узко.</td>
</tr>
</tbody>
</table>
<h3 id="_12">Варианты фикса</h3>
<ol>
<li><strong>Negative prompt (15 минут)</strong> — добавить в метапромпт сферы 3: <code>negative: "conference, corporate event, networking, business presentation, lectern, slideshow"</code>. Прямое подавление bias.</li>
<li><strong>Composition shift (час)</strong> — переписать дефолтные visual anchors сферы 3: убрать «лофт + аппаратура», заменить на «природа + круг людей + ковры». Меняем семантику визуала, не словарь.</li>
<li><strong>Hybrid</strong> — negative prompt + visual anchor diversity (3 типа retreat в ротации: природный / urban-loft / villa).</li>
</ol>
<h3 id="_13">Моя рекомендация</h3>
<p><strong>Negative prompt (1)</strong> для MVP, <strong>Hybrid (3)</strong> как следующая итерация. 15-минутный фикс выводит сферу из критики, потом улучшаем разнообразие в спринте post-MVP.</p>
<h3 id="_14">Что нужно от тебя</h3>
<ul>
<li>Подтвердить negative prompt вариант</li>
<li>(Опц.) дать пример «правильного» retreat-визуала — у тебя был референс?</li>
</ul>
<hr>
<h2 id="_15">Сводная матрица</h2>
<table>
<thead>
<tr>
<th>Баг</th>
<th>Severity</th>
<th>Слой</th>
<th>Effort</th>
<th>Зависимость</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>B2 Profile ERROR</strong></td>
<td>CRITICAL</td>
<td>Prompt-layer (OpenRouter)</td>
<td>0.5–1 день</td>
<td>блокирует identity continuity = ядро продукта</td>
</tr>
<tr>
<td><strong>B3 Wish-bypass</strong></td>
<td>HIGH</td>
<td>Orchestration (роутинг)</td>
<td>0.5 день</td>
<td>критичен для retention (wish = engagement)</td>
</tr>
<tr>
<td><strong>B4 Sphere 3 mismatch</strong></td>
<td>MEDIUM</td>
<td>FAL bias (компенсируется промтом)</td>
<td>15 минут</td>
<td>косметический, но видимый</td>
</tr>
</tbody>
</table>
<h3 id="2005">Предлагаемый порядок до 20.05</h3>
<ol>
<li><strong>B4</strong> — пятница вечер (15 мин, не зависит ни от кого, сразу убирает заметный mismatch)</li>
<li><strong>B3</strong> — суббота (полдня, моя зона — promt-engineering, тебе только утвердить wrapper-архитектуру)</li>
<li><strong>B2</strong> — воскресенье (день — Mid fix через composite style logic; самая большая ставка на качество MVP)</li>
<li><strong>B1 Paywall</strong> — понедельник (Денис)</li>
</ol>
<p>Если B2 окажется тяжелее за день — отрезаем мне scope: ставлю Soft fix (1), вытягиваем 85% случаев, остальное в post-MVP бэклог.</p>
<hr>
<h2 id="_16">Что я НЕ предлагаю</h2>
<ul>
<li>Не предлагаю переделывать <code>profile_summary</code> контракт (Hard fix B2) — это переделка с Денисом, не успеваем к 20.05.</li>
<li>Не предлагаю классифицировать wish-types (Hybrid B3) — лишняя сложность, MVP-плохо.</li>
<li>Не предлагаю переснимать визуалы sphere 3 (Hard fix B4) — пока не доказали что FAL bias не лечится negative prompt.</li>
</ul>
<hr>
<h2 id="_17">Открытые вопросы</h2>
<ol>
<li><strong>B2</strong>: per-occasion mapping — hardcode таблица 10×occasion или AI решает на месте?</li>
<li><strong>B3</strong>: индикатор «обрабатываю уточнение» — показывать или скрыть лишние 1-2 сек?</li>
<li><strong>B4</strong>: есть референс «правильного» retreat-визуала для образца?</li>
</ol>
<div class="footer">Elyne · документ опубликован для команды. Канон лежит в приватном репо Monada — здесь срез на момент публикации.</div>
</body>
</html>
