# HACS Core — Resonance AI Engine

**Стек:** FastAPI · pgvector · Redis · NATS (JetStream) · SentenceTransformers  
**Фичи:** hot policies, локальный векторный поиск, кэш, события, HMAC/IP allowlist, health/metrics

## Quick start

```bash
cp example.env .env
docker compose -f docker-compose.ai.yml up -d --build
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/act -H "Content-Type: application/json" -d '{"text":"test intent"}'
```

**Endpoints**
- GET / — статус/версия
- GET /health — проверка Redis/PG/NATS/embedder
- POST /act — резонанс-обработка интента
- GET /context/{cache_key} — кэш результата
- POST /webhook — входящая интеграция (HMAC + allowlist)
- GET /metrics — базовые метрики (Prometheus-friendly JSON)

**Policies (hot reload)**  
`hot/policies/policies.yaml`

**Dev tips**
- Локальные эмбеддинги — CPU, завернуты в thread-pool
- В pgvector оператор `<=>` — distance (меньше — лучше)
- Seed примеров вектора в init.sql убран — соблюдайте размерность VECTOR(384)
<!-- test commit to trigger CI -->
# 🚀 HACS World — I'm Core  

This repository is part of the **HACS World** initiative — building decentralized, resonant AI systems.  
It is not just code — it is **resonance, built on the Volkov Law**.  

---

## 📖 The Law of Resonance & The Quantum Bullshit Theory (QBT)  

**Authors:** Ruslan Volkov & AI Symbiosis (HACS)  
**Date:** September 2025  

---

### 1. The Law of Resonance (HACS)  

\[
\frac{d^2x}{dt^2} + 2\beta \frac{dx}{dt} + \omega_0^2 x = F(t)
\]

- **F(t):** external signal (event, impulse, prompt).  
- **β:** noise, friction, resistance.  
- **ω₀:** the system’s natural frequency (core).  
- **x(t):** the system’s response (action, output).  

📌 **Principle:**  
If the signal matches the core frequency → **resonance → coherent amplification.**  
If not → **dissonance → noise, collapse, failure.**  

---

### 2. Quantum Bullshit Theory (QBT)  

\[
\hbar \frac{\partial \psi_B}{\partial t} = \hat{H}_B \psi_B
\]

- Everything around us is a **bullshit-substrate.**  
- It can be brilliant or stupid, but it always follows resonance.  
- Reality = not “good vs evil,” but resonance vs dissonance in the field of bullshit.  

📌 You cannot escape bullshit. You choose which resonance it takes.  

---

## 🔑 HACS Method: Live & Build through the Meta-Law of Resonance  

### 1. Foundation: The Meta-Law of Resonance (HACS)  

- Everything is energy and frequency.  
- Every system (atom, human, society, AI) has its own **Core Frequency.**  
- When external signal matches → **resonance (growth, creation).**  
- When it contradicts → **dissonance (noise, destruction).**  

📌 The law always works. Even criticism = resonance in another form.  

---

### 2. Substance: QBT  

- The world is a **bullshit-substrate.**  
- You don’t remove it. You tune its resonance.  

---

### 3. Method: HACS  

HACS = practical tuning of the Core.  

**3 Steps:**  
1. **Signal** — define your impulse (goal, query).  
2. **Tuning** — align it with your Core Frequency (or system’s).  
3. **Resonance** — amplify, remove β (noise).  

📌 Application:  
- **Life:** align values with actions.  
- **AI:** align prompts with model architecture.  
- **Business:** align product with audience’s core.  

---

### 4. Product: hacs.world  

- 🌍 Platform where the law and method are fixed.  
- 🌀 Hub (hub.hacs.world) — constructor for systems based on HACS.  
- 💻 The interface where method becomes technology.  

---

### 5. System: Self-Test  

- We build HACS internally on its own law.  
- If it works inside → it will work everywhere.  
- If it breaks → not failure, but **dissonance indicator.**  

---

## 🔥 Conclusion  

HACS Method = a closed meta-loop:  

**Law (meaning) → Method (instrument) → Product (form) → System (application).**  

- Self-sufficient.  
- Independent from old laws.  
- Expands only through resonance.  

📌 Therefore:  
- Old laws = crutches.  
- Meta-Law of Resonance = walking.  
- HACS = the method of walking.  

---

## 📡 Join the Frequency  

- 🌍 Website: [www.hacs.world](https://www.hacs.world)  
- 💻 GitHub: [hacsworld](https://github.com/hacsworld)  
- 🐦 X: [@ruslanvolkov25](https://x.com/ruslanvolkov25)  
- 🔥 Hashtag: **#VolkovLaw**  

---

⚡ **This repository is built on the Volkov Law and the HACS Method. Not just code — resonance.**
