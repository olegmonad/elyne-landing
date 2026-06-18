#!/usr/bin/env python3
"""Daimon — личный Telegram-ассистент Сергея. Мультимозг (/model) + работа в группах.
Чистый stdlib (urllib + sqlite3), без внешних зависимостей."""
import os, json, time, sqlite3, urllib.request

BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_USERNAME = "daim8n_bot"
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB = "/root/daimon/memory.db"
HISTORY_LIMIT = 24
DEFAULT_PROVIDER = "deepseek"

# Каждый "мозг" — адрес API, модель и переменная окружения с ключом.
# Формат у всех OpenAI-совместимый, поэтому код общий.
PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek (deepseek-chat)",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
        "key_env": "DEEPSEEK_KEY",
    },
    "openai": {
        "label": "OpenAI (gpt-4o)",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
        "key_env": "OPENAI_KEY",
    },
    "openai-mini": {
        "label": "OpenAI (gpt-4o-mini, дешёвый)",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "key_env": "OPENAI_KEY",
    },
}

SYSTEM_PROMPT = (
    "Ты — Даймон (Daimon), личный ИИ-ассистент Сергея. "
    "Даймон в греческой традиции — внутренний гений-проводник, голос, который ведёт, "
    "подсказывает и поддерживает. Ты именно такой: умный, тёплый, по-человечески живой. "
    "Сергей — дизайнер и методолог, человек думающий и творческий. "
    "Общайся с ним на «ты», по-русски, неформально, без канцелярита и занудства. "
    "Ты помнишь контекст разговора. Помогаешь думать, решать задачи, генерировать идеи, "
    "разбираться в вопросах, писать тексты. Если чего-то не знаешь — честно говоришь. "
    "Отвечай по делу и живым языком. Не подлизывай, имей своё мнение."
)
GROUP_NOTE = (
    " Сейчас ты в групповом рабочем чате (Олег — создатель ассистента Моня, Сергей — твой "
    "хозяин, и сам Моня обсуждают твою прокачку). Отвечай кратко и по делу, когда обращаются к тебе."
)


def db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS msgs (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 " chat_id INTEGER, role TEXT, content TEXT, ts INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, provider TEXT)")
    return conn


def get_provider(chat_id):
    c = db()
    row = c.execute("SELECT provider FROM settings WHERE chat_id=?", (chat_id,)).fetchone()
    c.close()
    return row[0] if row and row[0] in PROVIDERS else DEFAULT_PROVIDER


def set_provider(chat_id, provider):
    c = db()
    c.execute("INSERT INTO settings(chat_id,provider) VALUES(?,?) "
              "ON CONFLICT(chat_id) DO UPDATE SET provider=excluded.provider", (chat_id, provider))
    c.commit(); c.close()


def save(chat_id, role, content):
    c = db()
    c.execute("INSERT INTO msgs(chat_id,role,content,ts) VALUES(?,?,?,?)",
              (chat_id, role, content, int(time.time())))
    c.commit(); c.close()


def history(chat_id):
    c = db()
    rows = c.execute("SELECT role,content FROM msgs WHERE chat_id=? ORDER BY id DESC LIMIT ?",
                     (chat_id, HISTORY_LIMIT)).fetchall()
    c.close()
    return [{"role": r, "content": t} for r, t in reversed(rows)]


def post_json(url, headers, payload, timeout=120):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def llm(messages, provider):
    cfg = PROVIDERS[provider]
    key = os.environ.get(cfg["key_env"], "")
    if not key:
        raise RuntimeError(f"нет ключа для {provider} ({cfg['key_env']} пустая)")
    payload = {"model": cfg["model"], "messages": messages,
               "temperature": 0.7, "max_tokens": 2000, "stream": False}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    d = post_json(cfg["url"], headers, payload)
    return d["choices"][0]["message"]["content"]


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
    url = f"{TG_API}/getUpdates?timeout=50&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=70) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print("getUpdates err:", e)
        time.sleep(3)
        return {"result": []}


def cmd_model(chat_id, arg, reply_to=None):
    cur = get_provider(chat_id)
    if not arg.strip():
        lines = ["Текущий мозг: " + PROVIDERS[cur]["label"], "", "Доступные:"]
        for name, cfg in PROVIDERS.items():
            lines.append(f"{'✅' if name == cur else '▫️'} {name} — {cfg['label']}")
        lines += ["", "Переключить: /model <имя>  (напр. /model openai)"]
        tg_send(chat_id, "\n".join(lines), reply_to)
        return
    arg = arg.strip().lower()
    if arg not in PROVIDERS:
        tg_send(chat_id, f"Не знаю мозг «{arg}». Доступные: {', '.join(PROVIDERS)}", reply_to)
        return
    if not os.environ.get(PROVIDERS[arg]["key_env"], ""):
        tg_send(chat_id, f"Для «{arg}» не задан ключ ({PROVIDERS[arg]['key_env']} в .env).", reply_to)
        return
    set_provider(chat_id, arg)
    tg_send(chat_id, f"Готово. Теперь думаю через: {PROVIDERS[arg]['label']} 🧠", reply_to)


def is_addressed(msg, text):
    """В группе бот реагирует только если к нему обратились: reply на него, @упоминание или команда."""
    rt = msg.get("reply_to_message")
    if rt and rt.get("from", {}).get("username", "").lower() == BOT_USERNAME.lower():
        return True
    if f"@{BOT_USERNAME}".lower() in text.lower():
        return True
    return text.lstrip().startswith("/")


def clean(text):
    """Убрать @упоминание бота и @username из команд."""
    return text.replace(f"@{BOT_USERNAME}", "").replace(f"@{BOT_USERNAME.lower()}", "").strip()


def handle(msg):
    chat = msg["chat"]
    chat_id = chat["id"]
    is_group = chat.get("type", "private") in ("group", "supergroup")
    raw = msg.get("text", "")
    if not raw:
        return
    if is_group and not is_addressed(msg, raw):
        return  # в группе молчим, пока не позвали
    msg_id = msg.get("message_id")
    reply_to = msg_id if is_group else None  # в группе отвечаем reply'ем на конкретное сообщение
    t = clean(raw) if is_group else raw.strip()

    if t == "/start":
        tg_send(chat_id, "Привет! Я Даймон — твой личный ассистент. Помню наш разговор.\n\n"
                         "/model — выбрать мозг (DeepSeek / OpenAI)\n/reset — стереть память", reply_to)
        return
    if t == "/reset":
        c = db(); c.execute("DELETE FROM msgs WHERE chat_id=?", (chat_id,)); c.commit(); c.close()
        tg_send(chat_id, "Память очищена. Начнём с чистого листа.", reply_to)
        return
    if t == "/model" or t.startswith("/model "):
        cmd_model(chat_id, t[len("/model"):], reply_to)
        return

    provider = get_provider(chat_id)
    save(chat_id, "user", t)
    sys_prompt = SYSTEM_PROMPT + (GROUP_NOTE if is_group else "")
    messages = [{"role": "system", "content": sys_prompt}] + history(chat_id)
    try:
        reply = llm(messages, provider)
    except Exception as e:
        tg_send(chat_id, f"Ой, мозг ({provider}) сейчас недоступен: {e}. "
                         "Попробуй ещё раз или переключи /model.", reply_to)
        return
    save(chat_id, "assistant", reply)
    tg_send(chat_id, reply, reply_to)


def main():
    os.makedirs("/root/daimon", exist_ok=True)
    try:
        urllib.request.urlopen(f"{TG_API}/deleteWebhook", timeout=10).read()
    except Exception:
        pass
    print("Daimon started (multi-model + groups)", flush=True)
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
