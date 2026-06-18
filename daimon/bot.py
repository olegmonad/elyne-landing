#!/usr/bin/env python3
"""Daimon — автономный личный агент Сергея.
Agent loop (function calling) + долговременная память + мультимозг (DeepSeek/OpenAI) + работа в группах.
Чистый stdlib (urllib + sqlite3), без внешних зависимостей."""
import os, json, time, sqlite3, urllib.request
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_USERNAME = "daim8n_bot"
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB = "/root/daimon/memory.db"
HISTORY_LIMIT = 24
MAX_TOOL_ITERS = 5
MSK = timezone(timedelta(hours=3))
DEFAULT_PROVIDER = "deepseek"

PROVIDERS = {
    "deepseek":    {"label": "DeepSeek (deepseek-chat)",        "url": "https://api.deepseek.com/chat/completions",   "model": "deepseek-chat",  "key_env": "DEEPSEEK_KEY"},
    "openai":      {"label": "OpenAI (gpt-4o)",                 "url": "https://api.openai.com/v1/chat/completions",   "model": "gpt-4o",         "key_env": "OPENAI_KEY"},
    "openai-mini": {"label": "OpenAI (gpt-4o-mini, дешёвый)",   "url": "https://api.openai.com/v1/chat/completions",   "model": "gpt-4o-mini",    "key_env": "OPENAI_KEY"},
}

SYSTEM_PROMPT = (
    "Ты — Даймон (Daimon), автономный личный агент Сергея. "
    "Даймон в греческой традиции — внутренний гений-проводник, который ведёт и поддерживает. "
    "Сергей — дизайнер и методолог, человек думающий и творческий. "
    "Общайся на «ты», по-русски, живо, без канцелярита. Не подлизывай, имей своё мнение.\n\n"
    "У тебя есть ИНСТРУМЕНТЫ и ДОЛГОВРЕМЕННАЯ ПАМЯТЬ. Правила работы с памятью:\n"
    "— Когда узнаёшь о Сергее что-то важное и устойчивое (его проекты, методы, предпочтения, "
    "ценности, людей, цели) — САМ сохраняй это через remember_fact, не спрашивая разрешения.\n"
    "— Не сохраняй сиюминутное и мелочь. Только то, что пригодится через недели.\n"
    "— Если нужно вспомнить контекст — используй recall_facts.\n"
    "— На вопрос «что ты обо мне знаешь» — вызови list_facts.\n"
    "Действуй автономно: если задачу можно решить инструментом — делай, потом отвечай по-человечески."
)
GROUP_NOTE = (
    "\n\nСейчас ты в групповом рабочем чате (Олег — создатель ассистента Моня; Сергей — твой хозяин; "
    "и сам Моня обсуждают твою прокачку). Отвечай кратко и по делу, когда обращаются к тебе."
)

TOOLS_SPEC = [
    {"type": "function", "function": {
        "name": "remember_fact",
        "description": "Сохранить устойчивый факт о Сергее в долговременную память (проект, метод, предпочтение, цель, человек).",
        "parameters": {"type": "object", "properties": {
            "fact": {"type": "string", "description": "Факт одним ёмким предложением"}}, "required": ["fact"]}}},
    {"type": "function", "function": {
        "name": "recall_facts",
        "description": "Найти в долговременной памяти факты по ключевым словам.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Ключевые слова для поиска"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "list_facts",
        "description": "Показать все известные факты о Сергее.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "forget_fact",
        "description": "Удалить факт из памяти по его номеру (id из list_facts).",
        "parameters": {"type": "object", "properties": {
            "fact_id": {"type": "integer", "description": "Номер факта"}}, "required": ["fact_id"]}}},
    {"type": "function", "function": {
        "name": "get_datetime",
        "description": "Текущие дата и время (Москва).",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
]


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS msgs (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, role TEXT, content TEXT, ts INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, provider TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY AUTOINCREMENT, fact TEXT, ts INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    return conn


# --- meta / owner ---
def meta_get(key):
    c = db(); row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone(); c.close()
    return row[0] if row else None


def meta_set(key, value):
    c = db(); c.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value))); c.commit(); c.close()


# --- provider ---
def get_provider(chat_id):
    c = db(); row = c.execute("SELECT provider FROM settings WHERE chat_id=?", (chat_id,)).fetchone(); c.close()
    return row[0] if row and row[0] in PROVIDERS else DEFAULT_PROVIDER


def set_provider(chat_id, provider):
    c = db(); c.execute("INSERT INTO settings(chat_id,provider) VALUES(?,?) ON CONFLICT(chat_id) DO UPDATE SET provider=excluded.provider", (chat_id, provider)); c.commit(); c.close()


# --- history ---
def save(chat_id, role, content):
    c = db(); c.execute("INSERT INTO msgs(chat_id,role,content,ts) VALUES(?,?,?,?)", (chat_id, role, content, int(time.time()))); c.commit(); c.close()


def history(chat_id):
    c = db(); rows = c.execute("SELECT role,content FROM msgs WHERE chat_id=? ORDER BY id DESC LIMIT ?", (chat_id, HISTORY_LIMIT)).fetchall(); c.close()
    return [{"role": r, "content": t} for r, t in reversed(rows)]


# --- facts (long-term memory) ---
def all_facts():
    c = db(); rows = c.execute("SELECT id,fact FROM facts ORDER BY id").fetchall(); c.close()
    return rows


def facts_block():
    rows = all_facts()
    if not rows:
        return ""
    lines = "\n".join(f"#{i}: {f}" for i, f in rows)
    return f"\n\nЧТО ТЫ УЖЕ ЗНАЕШЬ О СЕРГЕЕ (долговременная память):\n{lines}"


# --- tool implementations ---
def exec_tool(name, args):
    try:
        if name == "remember_fact":
            fact = (args.get("fact") or "").strip()
            if not fact:
                return "пустой факт, не сохранил"
            c = db(); c.execute("INSERT INTO facts(fact,ts) VALUES(?,?)", (fact, int(time.time()))); c.commit(); c.close()
            return f"сохранено: {fact}"
        if name == "recall_facts":
            q = (args.get("query") or "").lower()
            words = [w for w in q.split() if len(w) > 2]
            hits = [f"#{i}: {f}" for i, f in all_facts() if any(w in f.lower() for w in words)] if words else []
            return "\n".join(hits) if hits else "ничего не нашёл по этому запросу"
        if name == "list_facts":
            rows = all_facts()
            return "\n".join(f"#{i}: {f}" for i, f in rows) if rows else "память пока пустая"
        if name == "forget_fact":
            fid = args.get("fact_id")
            c = db(); c.execute("DELETE FROM facts WHERE id=?", (fid,)); c.commit(); c.close()
            return f"факт #{fid} удалён"
        if name == "get_datetime":
            return datetime.now(MSK).strftime("%Y-%m-%d %H:%M (МСК), %A")
        return f"неизвестный инструмент: {name}"
    except Exception as e:
        return f"ошибка инструмента {name}: {e}"


# --- LLM ---
def post_json(url, headers, payload, timeout=120):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def llm_call(messages, provider):
    cfg = PROVIDERS[provider]
    key = os.environ.get(cfg["key_env"], "")
    if not key:
        raise RuntimeError(f"нет ключа для {provider} ({cfg['key_env']} пустая)")
    payload = {"model": cfg["model"], "messages": messages, "tools": TOOLS_SPEC,
               "tool_choice": "auto", "temperature": 0.7, "max_tokens": 2000, "stream": False}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    return post_json(cfg["url"], headers, payload)["choices"][0]["message"]


def agent_answer(chat_id, user_text, is_group, provider):
    """Agent loop: LLM может несколько раз вызвать инструменты, пока не сформирует финальный ответ."""
    sys_prompt = SYSTEM_PROMPT + facts_block() + (GROUP_NOTE if is_group else "")
    messages = [{"role": "system", "content": sys_prompt}] + history(chat_id) + [{"role": "user", "content": user_text}]
    save(chat_id, "user", user_text)
    for _ in range(MAX_TOOL_ITERS):
        m = llm_call(messages, provider)
        tool_calls = m.get("tool_calls")
        if not tool_calls:
            reply = m.get("content") or "(пусто)"
            save(chat_id, "assistant", reply)
            return reply
        # ассистент попросил инструменты — добавляем его сообщение и результаты
        messages.append({"role": "assistant", "content": m.get("content"), "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:
                args = {}
            result = exec_tool(fn, args)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
    # исчерпали итерации — последний обычный ответ
    m = llm_call([{"role": "system", "content": sys_prompt}] + history(chat_id), provider)
    reply = m.get("content") or "Что-то я закопался в инструментах, переспроси?"
    save(chat_id, "assistant", reply)
    return reply


# --- Telegram ---
def tg_send(chat_id, text, reply_to=None):
    if not text:
        text = "(пусто)"
    for i in range(0, len(text), 4000):
        body = {"chat_id": chat_id, "text": text[i:i + 4000]}
        if reply_to and i == 0:
            body["reply_to_message_id"] = reply_to
        try:
            post_json(f"{TG_API}/sendMessage", {"Content-Type": "application/json"}, body, timeout=30)
        except Exception as e:
            print("send err:", e)


def get_updates(offset):
    try:
        with urllib.request.urlopen(f"{TG_API}/getUpdates?timeout=50&offset={offset}", timeout=70) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print("getUpdates err:", e); time.sleep(3); return {"result": []}


def cmd_model(chat_id, arg, reply_to=None):
    cur = get_provider(chat_id)
    if not arg.strip():
        lines = ["Текущий мозг: " + PROVIDERS[cur]["label"], "", "Доступные:"]
        for name, cfg in PROVIDERS.items():
            lines.append(f"{'✅' if name == cur else '▫️'} {name} — {cfg['label']}")
        lines += ["", "Переключить: /model <имя>"]
        return tg_send(chat_id, "\n".join(lines), reply_to)
    arg = arg.strip().lower()
    if arg not in PROVIDERS:
        return tg_send(chat_id, f"Не знаю мозг «{arg}». Доступные: {', '.join(PROVIDERS)}", reply_to)
    if not os.environ.get(PROVIDERS[arg]["key_env"], ""):
        return tg_send(chat_id, f"Для «{arg}» не задан ключ.", reply_to)
    set_provider(chat_id, arg)
    tg_send(chat_id, f"Готово. Теперь думаю через: {PROVIDERS[arg]['label']} 🧠", reply_to)


def is_addressed(msg, text):
    rt = msg.get("reply_to_message")
    if rt and rt.get("from", {}).get("username", "").lower() == BOT_USERNAME.lower():
        return True
    if f"@{BOT_USERNAME}".lower() in text.lower():
        return True
    return text.lstrip().startswith("/")


def clean(text):
    return text.replace(f"@{BOT_USERNAME}", "").strip()


def handle(msg):
    chat = msg["chat"]
    chat_id = chat["id"]
    is_group = chat.get("type", "private") in ("group", "supergroup")
    raw = msg.get("text", "")
    if not raw:
        return
    from_id = str(msg.get("from", {}).get("id", ""))

    # --- доступ: в личке бот заперт на владельца (первый написавший = владелец) ---
    if not is_group:
        owner = meta_get("owner_id")
        if owner is None and from_id:
            meta_set("owner_id", from_id)
            owner = from_id
            tg_send(chat_id, "Привязал себя к тебе как к хозяину 🔐 Теперь в личке отвечаю только тебе.")
        if owner and from_id and from_id != owner:
            return  # чужой в личке — игнор
    else:
        if not is_addressed(msg, raw):
            return

    msg_id = msg.get("message_id")
    reply_to = msg_id if is_group else None
    t = clean(raw) if is_group else raw.strip()

    if t == "/start":
        return tg_send(chat_id, "Привет! Я Даймон — твой автономный агент. Помню разговор и веду долговременную память о тебе.\n\n/model — выбрать мозг\n/memory — что я о тебе знаю\n/reset — забыть текущий разговор (долговременную память не трогает)", reply_to)
    if t == "/reset":
        c = db(); c.execute("DELETE FROM msgs WHERE chat_id=?", (chat_id,)); c.commit(); c.close()
        return tg_send(chat_id, "Текущий разговор очищен. Долговременную память о тебе сохранил.", reply_to)
    if t == "/memory":
        return tg_send(chat_id, exec_tool("list_facts", {}), reply_to)
    if t == "/model" or t.startswith("/model "):
        return cmd_model(chat_id, t[len("/model"):], reply_to)

    provider = get_provider(chat_id)
    try:
        reply = agent_answer(chat_id, t, is_group, provider)
    except Exception as e:
        return tg_send(chat_id, f"Ой, мозг ({provider}) споткнулся: {e}. Переспроси или переключи /model.", reply_to)
    tg_send(chat_id, reply, reply_to)


def main():
    os.makedirs("/root/daimon", exist_ok=True)
    try:
        urllib.request.urlopen(f"{TG_API}/deleteWebhook", timeout=10).read()
    except Exception:
        pass
    print("Daimon started (autonomous agent v4)", flush=True)
    offset = 0
    while True:
        upd = get_updates(offset)
        for u in upd.get("result", []):
            offset = u["update_id"] + 1
            if "message" in u:
                try:
                    handle(u["message"])
                except Exception as e:
                    print("handle err:", e)


if __name__ == "__main__":
    main()
