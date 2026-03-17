# 🚄 QT — Quick Tatkal Agent (v1)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Playwright](https://img.shields.io/badge/Automation-Playwright-green)


An automation-based assistant that helps streamline the IRCTC booking flow using Playwright, with a Flask UI and live logging system.

---

## ⚙️ Features

- 🔐 Manual login session handling
- ⚡ Fast form filling (sub-second passenger entry)
- 🎯 Precise timing (NTP synchronized)
- 📡 Live log streaming to UI
- 🧠 Robust fallback strategies for dynamic UI elements
- 🔁 Retry-safe booking flow handling

---

## 🖥️ UI (v1-ui branch)

- Input journey details from browser
- Start automation with one click
- View real-time logs (no terminal needed)

---

## 🏗️ Tech Stack

- Python
- Playwright (browser automation)
- Flask (backend UI)
- HTML + JS (frontend)

---

## 🚀 How to Run

```bash
pip install flask playwright ntplib pytz
playwright install
python app.py