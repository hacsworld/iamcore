# HACS Core (iamcore)

**Human AGI Core Symbiosis (HACS)** — локальное ядро-оркестратор.  
Его задача — дистиллировать суть, убирать шум и управлять внешними моделями и модулями.  

> AI = расходник.  
> Ядро = закон.  
> Всё остальное = плагины.

---

## 🚀 Быстрый старт

### Установка
```bash
git clone https://github.com/hacsworld/iamcore.git
cd iamcore
python3 -m venv .venv && source .venv/bin/activate
pip install -r core/requirements.txt
cp .env.example .env
```

### Запуск ядра
```bash
uvicorn core.app:app --host 127.0.0.1 --port 8000 --reload
```

Проверка:
```bash
curl -H "X-API-Key: changeme" http://127.0.0.1:8000/ping
```

---

## 📡 Контракты API

### Health
`GET /ping`  
→ `{"ok": true, "ts": 1726459200}`

### Capabilities
`GET /capabilities`  
Список доступных модулей и команд.

### Dispatch
`POST /events/dispatch`  
Единый вход для фронта и интеграций.
```json
{
  "text": "/wallet balance",
  "context": { "lang": "en", "ui": "mobile" }
}
```
Ответ:
```json
{
  "status": "OK",
  "messages": [
    { "role": "assistant", "text": "Balance: 50,000.80 USDT" },
    { "role": "system", "ui_action": { "open": "g.pay", "tab": "crypto" } }
  ]
}
```

### Chat (совместимость)
`POST /chat`  
Простой режим, возвращает только текст ответа.

---

## 🧩 Архитектура

```
iamcore/
 ├── core/              # ядро
 │   ├── app.py         # FastAPI + endpoints
 │   ├── router.py      # оркестратор событий
 │   ├── resonance.py   # закон резонанса (distiller)
 │   ├── memory.py      # локальная векторная память
 │   ├── policy.py      # системные правила
 │   ├── policies.yaml  # словарь политик
 │   ├── providers.py   # OpenAI/Grok/Ollama адаптеры
 │   ├── readers.py     # чтение файлов
 │   ├── generation.py  # генерация ответов
 │   ├── humor.py       # модуль юмора
 │   ├── privacy.py     # обработка приватности
 │   ├── requirements.txt
 │   ├── Dockerfile
 │   └── start.sh
 ├── scripts/
 │   ├── sanity.sh      # быстрый тест ядра
 │   └── install_macos.sh
 ├── .env.example
 ├── Makefile
 ├── README.md
 ├── .gitignore
 └── state/             # (память, авто-создаётся)
```

---

## 🖥️ Интеграция во фронт

### 1. Детект локального ядра
```js
async function detectLocalCore() {
  const ports = [8000, 8001];
  for (const port of ports) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/ping`, {
        headers: { "X-API-Key": "changeme" },
      });
      if (res.ok) return `http://127.0.0.1:${port}`;
    } catch {}
  }
  return null;
}
```

### 2. Вызов ядра
```js
async function hacsDispatch(text) {
  const base = await detectLocalCore();
  if (!base) throw new Error("Core not found");

  const res = await fetch(`${base}/events/dispatch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": "changeme",
    },
    body: JSON.stringify({ text, context: { lang: "en" } }),
  });

  return res.json();
}
```

### 3. Обработка UI-экшенов
```js
const out = await hacsDispatch("/wallet balance");
out.messages.forEach(msg => {
  if (msg.ui_action) {
    // открыть нужный модуль, например G-Pay
    openUI(msg.ui_action);
  }
});
```

---

## 🔌 Плагины
Плагины подключаются через `ui_action` и/или registry.  
Примеры:
- G-Pay → `/wallet`, `/deposit`, `/withdraw`
- G-Market → `/market`, `/search`

Плагины лучше держать в отдельном репозитории (`hacs-plugins`).

---

## 🌀 Идеология

- AI модели → заменяемые модули (OpenAI, Grok, Ollama).  
- Ядро → одно, локальное, живёт у пользователя.  
- Резонанс → всегда вшит, даже без внешнего AI.  
- Всё работает через **один чат**, остальное — плагины вокруг.  

---

## ✅ TODO
- [ ] Тесты в `tests/`
- [ ] WS `/ws` для real-time чата
- [ ] Registry для плагинов
- [ ] Память автосинх в облако

---

Voice of the Future 🌍  
HACS Core — твой личный AGI-движок.
