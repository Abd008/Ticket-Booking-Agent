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