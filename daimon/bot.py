#!/usr/bin/env python3
"""Daimon — личный Telegram-ассистент Сергея. Несколько мозгов с переключением /model.
Чистый stdlib (urllib + sqlite3), без внешних зависимостей."""
import os, json, time, sqlite3, urllib.request

BOT_TOKEN = os.environ["BOT_TOKEN"]
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB = "/root/daimon/memory.db"
HISTORY_LIMIT = 24
DEFAULT_PROVIDER = "deepseek"

# Каждый "мозг" — это адрес API, модель и переменная окружения с ключом.
# Формат у всех одинаковый (OpenAI-совместимый), поэтому код общий.
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


def db():
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS msgs (id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " chat_id INTEGER, role TEXT, content TEXT, ts INTEGER)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS settings (chat_id INTEGER PRIMARY KEY, provider TEXT)")
    return conn


def get_provider(chat_id):
    c = db()
    row = c.execute("SELECT provider FROM settings WHERE chat_id=?", (chat_id,)).fetchone()
    c.close()
    if row and row[0] in PROVIDERS:
        return row[0]
    return DEFAULT_PROVIDER


def set_provider(chat_id, provider):
    c = db()
    c.execute("INSERT INTO settings(chat_id,provider) VALUES(?,?) "
              "ON CONFLICT(chat_id) DO UPDATE SET provider=excluded.provider",
              (chat_id, provider))
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
        raise RuntimeError(f"нет ключа для {provider} (переменная {cfg['key_env']} пустая)")
    payload = {"model": cfg["model"], "messages": messages,
               "temperature": 0.7, "max_tokens": 2000, "stream": False}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    d = post_json(cfg["url"], headers, payload)
    return d["choices"][0]["message"]["content"]


def tg_send(chat_id, text):
    if not text:
        text = "(пусто)"
    for i in range(0, len(text), 4000):
        try:
            post_json(f"{TG_API}/sendMessage", {"Content-Type": "application/json"},
                      {"chat_id": chat_id, "text": text[i:i + 4000]}, timeout=30)
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


def cmd_model(chat_id, arg):
    cur = get_provider(chat_id)
    if not arg:
        lines = ["Текущий мозг: " + PROVIDERS[cur]["label"], "", "Доступные:"]
        for name, cfg in PROVIDERS.items():
            mark = "✅" if name == cur else "▫️"
            lines.append(f"{mark} {name} — {cfg['label']}")
        lines.append("")
        lines.append("Переключить: /model <имя>  (напр. /model openai)")
        tg_send(chat_id, "\n".join(lines))
        return
    arg = arg.strip().lower()
    if arg not in PROVIDERS:
        tg_send(chat_id, f"Не знаю мозг «{arg}». Доступные: {', '.join(PROVIDERS)}")
        return
    key = os.environ.get(PROVIDERS[arg]["key_env"], "")
    if not key:
        tg_send(chat_id, f"Для «{arg}» не задан ключ ({PROVIDERS[arg]['key_env']} в .env). "
                         "Добавь ключ и перезапусти бота.")
        return
    set_provider(chat_id, arg)
    tg_send(chat_id, f"Готово. Теперь думаю через: {PROVIDERS[arg]['label']} 🧠")


def handle(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    if not text:
        return
    t = text.strip()
    if t == "/start":
        tg_send(chat_id, "Привет! Я Даймон — твой личный ассистент. "
                         "Помню наш разговор.\n\n/model — выбрать мозг (DeepSeek / OpenAI)\n"
                         "/reset — стереть память")
        return
    if t == "/reset":
        c = db(); c.execute("DELETE FROM msgs WHERE chat_id=?", (chat_id,))
        c.commit(); c.close()
        tg_send(chat_id, "Память очищена. Начнём с чистого листа.")
        return
    if t == "/model" or t.startswith("/model "):
        cmd_model(chat_id, t[len("/model"):])
        return
    provider = get_provider(chat_id)
    save(chat_id, "user", text)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history(chat_id)
    try:
        reply = llm(messages, provider)
    except Exception as e:
        tg_send(chat_id, f"Ой, мозг ({provider}) сейчас недоступен: {e}. "
                         "Попробуй ещё раз или переключи /model.")
        return
    save(chat_id, "assistant", reply)
    tg_send(chat_id, reply)


def main():
    os.makedirs("/root/daimon", exist_ok=True)
    try:
        urllib.request.urlopen(f"{TG_API}/deleteWebhook", timeout=10).read()
    except Exception:
        pass
    print("Daimon started (multi-model)", flush=True)
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
