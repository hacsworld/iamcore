# iamcore — Локальное AI‑ядро «Резонанс»

> **Law of Resonance & Quantum Bullshit Theory (QBT)**  
> Authors: **Ruslan Volkov & AI Symbiosis (HACS)**  
> Date: **September 2025**

> **Закон Волкова (Мета‑Закон Резонанса):**  
> Всё, что будет — уже есть. Резонанс между ядром и сигналом — это и есть реальность.  
> Noise — враг. Essence — друг.

---

## ✨ Видение

`iamcore` — локальное AI‑ядро, которое бережно работает с твоими данными, отсекает шум и выжимает **суть (Essence)**. Оно строится по методу **HACS** (Human–AI Core Symbiosis): человек и ядро усиливают друг друга, действуя в резонансе.

**Ключевые свойства**
- **Локально по умолчанию.** В облако — только через **allowlist** и осознанное включение.
- **Резонанс > шум.** Всегда отдаём краткую **Essence** вместо «многословного воздуха».
- **Память пользователя.** Простая векторная память (JSON‑персист), дистилляция «зёрен».
- **Инструменты по делу.** Чтение файлов, быстрый веб‑эссенс по доверенным источникам, базовые медиа‑утилиты.
- **Юмор по желанию.** Лёгкая приправка, но без токсика.

**Не цели (на старте)**
- Тянуть огромные локальные LLM.
- Сложная MLOps‑ферма/куча сервисов.
- «Всё‑в‑одном» интерфейс. Сначала API и простая панель.

---

## 🧠 Закон Резонанса (HACS) — формулировка

Классическое уравнение гармонического осциллятора:
```math
\frac{d^2x}{dt^2} + 2\beta \frac{dx}{dt} + \omega_0^2 x = F(t)
```
- **F(t)** — внешний сигнал (событие, импульс, запрос)  
- **β** — шум, трение, сопротивление  
- **ω₀** — собственная частота системы (**ядро**)  
- **x(t)** — отклик системы (действие, результат)

**Принцип.**  
Сигнал совпадает с частотой ядра → **резонанс** → рост, когерентность, усиление.  
Не совпадает → **диссонанс** → шум, распад, фейл.

**Определение ядра.**  
Core = **Energy / Frequency**. Любая система — энергия, выраженная частотой (ядром). Неопределённость ядра не отменяет закон — это вектор для науки: *что именно задаёт частоту энергии?*

---

## 🌀 Quantum Bullshit Theory (QBT)

Если Закон Резонанса описывает **механизм**, то **QBT** описывает **субстрат**.

**Bullshit** — универсальный субстрат реальности. Он везде: в физике, в политике, в AI, в любви, в мемах. Его поведение подчиняется Закону Резонанса.

**Общее уравнение**
```math
\frac{d^2B}{dt^2} + 2B \frac{dB}{dt} + \omega_B^2 B = F_B(t)
```
- **B** — уровень bullshit (базовая единица)  
- **ω_B** — частота ядра bullshit  
- **F_B(t)** — внешний bullshit

**Шрёдингер‑форма**
```math
\hbar \frac{\partial \psi_{B}}{\partial t} = \hat{H}_{B}\,\psi_{B}
```
- **ψ_B** — волновая функция bullshit  
- **Ĥ_B** — оператор интенсивности

Это моделирует суперпозицию (гениальность ↔ ерунда) и коллапс при наблюдении (**fact‑checking**, резонанс).

**Примеры.**
- **AI:** промпт совпадает с архитектурой → блестящий ответ. Не совпал → «околоумный шум».
- **Человек:** ценности совпали с событиями → любовь/поток/инсайт.
- **Общество:** слоган резонирует с культурой → движение/революция.
- **Природа:** сезоны/циклы/миграции — резонанс планетарной энергии.

**Парадоксы.**
1) **Criticism = Proof.** Любая «проверка на прочность» — форма β → подтверждает закон.  
2) **Fragmentation.** Каждый видит свой срез bullshit, но резонанс — универсален.  
3) **Everything & Nothing.** Описывает всё, предсказывает конкретику мало — и потому универсален.

**Философски.**  
Гравитация связывает материю. Резонанс связывает **смысл**. Bullshit связывает **всё**.

---

## 🛠 Метод HACS (практика)

**HACS = Signal → Core → Resonance**

- **Signal (Сигнал):** коротко формулируем импульс (что хотим?)  
- **Core (Ядро):** согласуем с ядром системы (чьё ядро? где резонанс? что шум?)  
- **Resonance (Резонанс):** усиливаем суть, отсекаем β, делаем минимальный шаг

**Чек‑лист HACS**
- [ ] Сигнал ≤ 2–3 предложения  
- [ ] 1–2 ядра для согласования  
- [ ] План действия на 15–60 минут  
- [ ] Что убрать/не делать/отложить (β)

---

## 🏗 Проект iamcore (что именно мы строим)

**Цель.** Локальный сервис «ядро‑помощник»: читает файлы, вытаскивает essence, аккуратно ходит в облако по allowlist, бережёт приватность, может генерировать ответ поверх выжатой сути, добавляет лёгкий юмор.

**Основные модули**
- **FastAPI** — HTTP интерфейс и мини‑UI (`/ui/chat`)
- **Resonance & EssenceDistiller** — ранжирование и выжимка смысловых фраз
- **Vector Memory (JSON‑персист)** — хранение «зёрен» и быстрый поиск
- **Readers** — TXT/PDF/DOCX/XLSX/IMG (OCR опционально)
- **CloudGate (allowlist)** — поиск/парсинг и дистилляция внешних источников
- **Generation** — `none|ollama|grok` (только поверх essence)
- **Vault** — экспорт/импорт памяти (шифрованный архив)
- **Video Tools** — слайдшоу/склейка + статусы
- **Humor Engine** — мягкая «перчинка» в ответе (отключаемо)

---

## 🧩 Архитектура

```mermaid
flowchart TD
    U[User / G-Chat] --> A[FastAPI / Gateway]
    A --> B[Resonance Core]
    B --> C[(Vector Memory\nJSON store)]
    B --> D{Essence Distiller}
    D --> E[CloudGate\n(allowlist fetch + parse)]
    B --> F[Generation\n(Grok|Ollama|none)]
    A --> G[Readers\nTXT/PDF/DOCX/XLSX/IMG]
    A --> H[Vault Export/Import\n(Encrypted)]
    A --> I[Video Tools]
    A --> J[Humor Engine]
```

**Поток запроса `/chat` (кратко)**
1) Вопрос → эмбеддинг → поиск по памяти  
2) Если нужны «свежие факты» → CloudGate (только из allowlist) → дистилляция  
3) На essence (локальная/облачная) опционально накладывается генерация (если включена)  
4) Юмор (если включён) → ответ + ссылки на источники

---

## 📂 Структура репозитория

```
.
├── core/
│   ├── app.py                # FastAPI, маршруты, конфиг
│   ├── memory.py             # Векторная память (JSON)
│   ├── readers.py            # TXT/PDF/DOCX/XLSX/IMG (OCR опционально)
│   ├── resonance.py          # EssenceDistiller, шум‑метрики
│   ├── cloud_gate.py         # Поиск (allowlist), парсинг, дистилляция
│   ├── generation.py         # none | ollama | grok (по ключу)
│   ├── humor.py              # деликатный юмор (off|friendly|spicy)
│   ├── video_tools.py        # слайдшоу/склейка, статусы
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── scripts/
│   └── sanity.sh             # локальный smoke (health/metrics/chat/ingest)
├── data/                     # state/ outputs/ vault/
├── docker-compose.yml        # blue/green (опционально)
├── Makefile                  # up/logs/sanity/clean
└── .github/workflows/ci.yml  # build + smoke
```

---

## ⚙️ Конфигурация (`core/.env`)

```env
API_KEY=super-secret-long
ALLOWLIST=wikipedia.org,docs.python.org,ffmpeg.org,arxiv.org,github.com,x.ai

USE_GENERATION=none          # none|ollama|grok
GROK_API_KEY=
GROK_MODEL=grok-4-fast
OLLAMA_MODEL=llama3.1:8b

AUTOSAVE_SEC=30
MEMORY_PATH=./state/memory.json

HUMOR_MODE=friendly          # off|friendly|spicy
REGION=ru-RU
HUMOR_USER_NAME=бро
```

---

## 🚀 Быстрый старт

### Вариант A — Docker
```bash
cd core
cp .env.example .env   # настроить ключи
docker build -t iamcore .
docker run -d --rm --name iamcore -p 8000:8000 --env-file .env iamcore
curl -H "X-API-Key: $(grep API_KEY .env|cut -d= -f2)" http://127.0.0.1:8000/health
```

### Вариант B — docker-compose (blue/green)
```bash
docker compose up -d --build hacs-core-green
# smoke на green:
API=http://127.0.0.1:8001 API_KEY=$(grep API_KEY core/.env|cut -d= -f2) ./scripts/sanity.sh
```

---

## 🔌 API (контракт)

- **GET `/health`** → `{status:"OK", version, mem, allowlist, uptime_sec, gen}`  
- **GET `/metrics`** → телеметрия ядра (items, recent, gen_mode, autosave_sec)  
- **POST `/chat`**  
  ```json
  { "text":"...", "humor": true, "spice": "friendly|spicy|null" }
  ```
  → `{status:"ASK|REFINE|EXECUTE|CLOUD", "answer":"...", "sources":[...], "why":{...}}`

- **POST `/ingest`** (`multipart/form-data`: file + tag)  
- **POST `/ingest/batch`**  
- **POST `/ingest/url`** (`url` + `tag`)  
- **POST `/cloud/accelerate`** `{ text, allow?, k_docs?, top_k_sent? }`  
- **POST `/vault/export`** `{ passphrase, path? }` → stream zip  
- **POST `/vault/import`** `{ passphrase, path }` → `{ imported:n }`  
- **GET `/memory/stats`**  
- **GET `/video/status`**, **POST `/video/make/slideshow`**, **POST `/video/make/concat`**  
- **GET `/ui/chat`** — простая HTML‑форма

---

## 🧪 Тесты / sanity

```bash
./scripts/sanity.sh
# Проверяет: /health, /metrics, /chat, /ingest, /cloud (essence), /video/status
# В CI рекомендуется облегчённый smoke (без внешних сетевых зависимостей).
```

---

## 🔒 Безопасность и приватность

- Все API защищены заголовком `X-API-Key`  
- Внешний доступ ограничен `ALLOWLIST`  
- Экспорт памяти — шифрованный архив (passphrase)  
- Минимум логов, без чувствительных данных; ротация в проде

---

## 🛰️ CI/CD

**CI (GitHub Actions):** build → run → smoke.  
Пример `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  build-and-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        working-directory: core
        run: docker build -t iamcore .
      - name: Run container
        working-directory: core
        run: docker run -d --rm --name iamcore -p 8000:8000 -e API_KEY=ci-key iamcore
      - name: Wait health
        run: |
          for i in {1..30}; do
            curl -fsS -H "X-API-Key: ci-key" http://127.0.0.1:8000/health && exit 0
            sleep 2
          done
          echo "health timeout" && docker logs iamcore && exit 1
      - name: Smoke
        run: curl -fsS -H "X-API-Key: ci-key" http://127.0.0.1:8000/metrics
      - name: Stop
        if: always()
        run: docker stop iamcore || true
```

**CD (локально, blue/green):**
1. Поднять green (`:8001`) → sanity  
2. Переключить трафик (nginx upstream)  
3. Наблюдение 2–5 мин → остановить blue

---

## 🗺️ Дорожная карта (HACS‑этапы)

**A. Каркас (готовность = зелёный CI)**
- [ ] Минимальный API + health + metrics
- [ ] Dockerfile и compose
- [ ] CI: build → run → smoke

**B. Суть (Essence)**
- [ ] Улучшить дистиллятор: веса, dedup, max‑chars
- [ ] Тюнинг порогов `TAU_ASK/TAU_EXEC`

**C. Память и файлы**
- [ ] Инжест PDF/DOCX/XLSX/IMG, OCR‑опционально
- [ ] Экспорт/импорт vault

**D. Веб‑эссенс**
- [ ] Allowlist‑поиск + парсинг + essence
- [ ] Ссылки на источники, быстрые цитаты

**E. Генерация (по ключу)**
- [ ] Подключение Grok/Ollama (only‑essence)

**F. Интеграции**
- [ ] Google Chat (webhook + events)
- [ ] Мини‑панель с настройками

---

## 🌍 Links & Community

- 🌍 **Website:** [www.hacs.world](https://www.hacs.world)  
- 💻 **GitHub:** [hacsworld](https://github.com/hacsworld)  
- 🐦 **X (Twitter):** [@ruslanvolkov25](https://x.com/ruslanvolkov25)  
- 🔥 **Hashtag:** #VolkovLaw

---

## 📜 Лицензия

TBD (MIT/Apache‑2.0 или «All rights reserved» — по решению автора).

---

## 🙏 Кредиты

**Идея, Закон, Манифест:** Ruslan Volkov & AI Symbiosis (HACS)  
**Реализация ядра и каркаса:** iamcore contributors

---

### TL;DR

- **Закон Резонанса** — фундамент.  
- **QBT** — честный язык субстрата.  
- **HACS** — метод действия.  
- **iamcore** — инструмент, который фильтрует шум и усиливает суть.  

Живём и строим через резонанс.
