# QT — Quick Tatkal Agent
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Playwright](https://img.shields.io/badge/Automation-Playwright-green)

Hybrid semi-automated assistant for IRCTC Tatkal booking.

This project demonstrates browser automation using Playwright to accelerate the booking workflow while keeping CAPTCHA and payment under human control.

---

## Features

- Precision timed search
- Automatic train detection and class selection
- Passenger autofill (~0.1s)
- Insurance handling
- Human-in-the-loop CAPTCHA stage
- Manual payment completion

---

## Ethical Design

- No CAPTCHA bypass
- No multiple account automation
- Human confirmation for sensitive steps
- Educational project
# QT — Quick Tatkal Agent

A hybrid semi-automated agent to assist with 
IRCTC Tatkal ticket booking.

## What it does
- Auto fills search form with precision timing
- Finds train and selects class automatically  
- Fills passenger details in ~0.09 seconds
- Hands over to human for CAPTCHA and payment

## Ethical Design
- No CAPTCHA bypass
- No multiple accounts
- Human in loop for all sensitive actions
- Personal use only

## Setup
pip install -r requirements.txt
python -m playwright install chromium
python main.py

## Disclaimer
Educational project. Not intended to 
exploit or cheat any systems.
