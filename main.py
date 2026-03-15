# -*- coding: utf-8 -*-
# main.py
# QT — Quick Tatkal Agent v1.0
# Author: Abd008

from playwright.sync_api import sync_playwright, TimeoutError
import time
import pytz
import ntplib
from datetime import datetime
import winsound

# ============================================
# CONFIGURATION
# ============================================

config = {
    "from_station": "SBC",
    "to_station":   "TLG",
    "date":         "18/03/2026",
    "quota":        "GENERAL",
    "train_number": "16227",
    "travel_class": "SL",

    "passengers": [
        {
            "name":   "JOHN DOE",
            "age":    "21",
            "gender": "M",
            "berth":  "LB",
        }
    ],

    "mobile": "9999999999",

    "search_at": {"hour": 0, "min": 0, "sec": 0},
    "book_at":   {"hour": 0, "min": 0, "sec": 5},

    "test_mode": True,
}

# ============================================
# UTILITIES
# ============================================

def beep(times=3):
    for _ in range(times):
        winsound.Beep(1000, 300)
        time.sleep(0.1)

def log(msg):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist).strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now}] {msg}")

def get_ntp_offset():
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org', version=3)
        offset = response.tx_time - time.time()
        log(f"⏱ NTP offset: {offset:.3f}s")
        return offset
    except:
        log("⚠️ NTP sync failed, using system clock")
        return 0

def get_ist_now(offset=0):
    ist = pytz.timezone('Asia/Kolkata')
    corrected = time.time() + offset
    return datetime.fromtimestamp(corrected, tz=ist)

# ============================================
# PRECISION TIMER
# ============================================

def wait_until(target, offset=0):
    log(f"⏳ Waiting for {target['hour']:02d}:{target['min']:02d}:{target['sec']:02d} IST...")

    while True:
        now = get_ist_now(offset)
        remaining = (
            target['hour'] * 3600 +
            target['min']  * 60   +
            target['sec']
        ) - (
            now.hour * 3600 +
            now.minute * 60 +
            now.second
        )

        if remaining <= 0:
            log("🚀 TIME — firing now!")
            break
        elif remaining <= 10:
            print(f"\r⚡ {remaining:.1f}s...", end="")
            time.sleep(0.05)
        elif remaining <= 60:
            print(f"\r⏰ {remaining}s remaining...", end="")
            time.sleep(0.5)
        else:
            print(f"\r⏰ {remaining}s remaining...", end="")
            time.sleep(2)

# ============================================
# MODULE 1 — LOGIN (MANUAL)
# ============================================

def login(page):
    log("🔐 Opening IRCTC...")

    page.goto(
        "https://www.irctc.co.in/nget/train-search",
        wait_until="domcontentloaded",
        timeout=60000
    )
    time.sleep(3)

    print("\n" + "="*50)
    print("👤 Please LOGIN manually in browser")
    print("   Wait until MY ACCOUNT appears top right")
    print("   Then press ENTER here")
    print("="*50)
    input()

    time.sleep(2)

    logged_in = False
    for selector in [
        "a[title='My Account']",
        "span:has-text('My Account')",
        "li:has-text('MY ACCOUNT')",
        "a:has-text('MY ACCOUNT')",
        ".username",
        "span.user-name"
    ]:
        if page.locator(selector).count() > 0:
            log(f"✅ Login verified via: {selector}")
            logged_in = True
            break

    if not logged_in:
        log("⚠️ Cannot verify login automatically")
        input("Press ENTER when fully logged in...")

    log("✅ Session established")
    return True

# ============================================
# MODULE 2 — PRE-FILL SEARCH FORM
# ============================================

def prefill_search(page, cfg):
    log("📝 Pre-filling search form...")

    try:
        from_input = page.locator(
            "input[aria-label='Enter From station. Input is Mandatory.']"
        )
        from_input.click()
        time.sleep(0.5)
        from_input.fill("")
        from_input.type(cfg['from_station'])
        time.sleep(3)

        from_options = page.locator("li.ui-autocomplete-list-item")
        log(f"From options found: {from_options.count()}")
        for i in range(from_options.count()):
            text = from_options.nth(i).inner_text()
            log(f"Option {i}: {text}")
            if cfg['from_station'] in text:
                from_options.nth(i).click(force=True)
                log(f"Clicked: {text}")
                break
        time.sleep(1)

        to_input = page.locator(
            "input[aria-label='Enter To station. Input is Mandatory.']"
        )
        to_input.click()
        time.sleep(0.5)
        to_input.fill("")
        to_input.type(cfg['to_station'])
        time.sleep(3)

        to_options = page.locator("li.ui-autocomplete-list-item")
        log(f"To options found: {to_options.count()}")
        for i in range(to_options.count()):
            text = to_options.nth(i).inner_text()
            log(f"Option {i}: {text}")
            if cfg['to_station'] in text:
                to_options.nth(i).click(force=True)
                log(f"Clicked: {text}")
                break
        time.sleep(1)

        from_val = from_input.input_value()
        to_val = to_input.input_value()
        log(f"From filled: {from_val}")
        log(f"To filled: {to_val}")

        date_input = page.locator("input.ui-inputtext").nth(2)
        date_input.click()
        time.sleep(0.5)
        date_input.press("Control+a")
        date_input.type(cfg['date'])
        time.sleep(0.5)
        page.keyboard.press("Escape")
        time.sleep(0.5)

        page.locator("div.ui-dropdown").nth(1).click()
        time.sleep(1)

        options = page.locator(".ui-dropdown-item")
        log(f"Quota options found: {options.count()}")
        for i in range(options.count()):
            text = options.nth(i).inner_text()
            log(f"Quota option {i}: {text}")

        clicked = False
        for i in range(options.count()):
            text = options.nth(i).inner_text()
            if cfg['quota'] in text:
                options.nth(i).click()
                log(f"✅ Quota selected: {text}")
                clicked = True
                break

        if not clicked:
            log("⚠️ Quota not found — pressing Escape")
            page.keyboard.press("Escape")

        time.sleep(0.5)
        log("✅ Search form pre-filled")
        return True

    except Exception as e:
        log(f"❌ Pre-fill failed: {e}")
        return False

# ============================================
# MODULE 3 — KEEP SESSION ALIVE
# ============================================

def keep_alive(page, until_time, offset=0):
    log("💓 Keep-alive started...")

    while True:
        now = get_ist_now(offset)
        remaining = (
            until_time['hour'] * 3600 +
            until_time['min']  * 60   +
            until_time['sec']
        ) - (
            now.hour * 3600 +
            now.minute * 60 +
            now.second
        )

        if remaining <= 15:
            log("⚡ Exiting keep-alive — search imminent")
            break

        page.evaluate("window.scrollBy(0, 1)")
        page.evaluate("window.scrollBy(0, -1)")
        log(f"💓 Session alive — {remaining}s to search")
        time.sleep(45)

# ============================================
# MODULE 4 — SEARCH AND SELECT TRAIN
# ============================================

def search_and_select(page, cfg):
    log("🔍 Firing search...")

    try:
        from_val = page.locator(
            "input[aria-label='Enter From station. Input is Mandatory.']"
        ).input_value()
        to_val = page.locator(
            "input[aria-label='Enter To station. Input is Mandatory.']"
        ).input_value()
        log(f"From: '{from_val}' | To: '{to_val}'")

        btn = page.locator("button:has-text('Search Trains')")
        log(f"Search btn found: {btn.count()} | disabled: {btn.is_disabled()}")

        btn.click()
        time.sleep(2)
        log(f"URL after search: {page.url}")

        page.wait_for_selector(
            "div.train-heading",
            timeout=60000
        )
        log("✅ Results loaded")
        time.sleep(2)

        train = page.locator(
            f"div.train-heading:has-text('{cfg['train_number']}')"
        ).first
        train.scroll_into_view_if_needed()
        log(f"🚂 Found train {cfg['train_number']}")
        time.sleep(1)

        train_row = page.locator(
            f"div:has(div.train-heading:has-text('{cfg['train_number']}'))"
        ).first

        # Click SL tab
        sl_clicked = False

        try:
            sl_btn = train_row.locator(
                "div.pre-avl:has-text('Sleeper')"
            )
            log(f"SL pre-avl found: {sl_btn.count()}")
            if sl_btn.count() > 0:
                sl_btn.first.click()
                time.sleep(2)
                all_cells = page.locator("div.pre-avl")
                for i in range(all_cells.count()):
                    text = all_cells.nth(i).inner_text()
                    if "Mar" in text or "Apr" in text:
                        log("✅ SL tab clicked — approach 1 verified")
                        sl_clicked = True
                        break
        except Exception as e:
            log(f"Approach 1 error: {e}")

        if not sl_clicked:
            try:
                sl_btn = page.locator(
                    "div.pre-avl:has-text('Sleeper')"
                )
                if sl_btn.count() > 0:
                    sl_btn.first.click(force=True)
                    time.sleep(2)
                    all_cells = page.locator("div.pre-avl")
                    for i in range(all_cells.count()):
                        text = all_cells.nth(i).inner_text()
                        if "Mar" in text or "Apr" in text:
                            log("✅ SL tab clicked — approach 2 verified")
                            sl_clicked = True
                            break
            except Exception as e:
                log(f"Approach 2 error: {e}")

        if not sl_clicked:
            try:
                page.evaluate("""
                    var divs = document.querySelectorAll('div.pre-avl');
                    for(var d of divs){
                        if(d.innerText.includes('Sleeper')){
                            d.click();
                            break;
                        }
                    }
                """)
                time.sleep(2)
                all_cells = page.locator("div.pre-avl")
                for i in range(all_cells.count()):
                    text = all_cells.nth(i).inner_text()
                    if "Mar" in text or "Apr" in text:
                        log("✅ SL tab clicked — approach 3 verified")
                        sl_clicked = True
                        break
            except Exception as e:
                log(f"Approach 3 error: {e}")

        if not sl_clicked:
            log("⚠️ Please click Sleeper (SL) tab manually")
            input("Press ENTER after clicking SL tab...")

        # Wait for date cells
        log("📅 Waiting for date cells to load...")
        for wait in range(10):
            cells = page.locator("div.pre-avl")
            date_found = False
            for i in range(cells.count()):
                text = cells.nth(i).inner_text()
                if "Mar" in text or "Apr" in text:
                    date_found = True
                    break
            if date_found:
                log("✅ Date cells ready")
                break
            time.sleep(1)
            log(f"Waiting... {wait+1}s")
        else:
            log("⚠️ Dates not loading — click SL manually")
            input("Click SL tab then press ENTER...")

        time.sleep(0.5)

        # Click correct date
        date_cells = page.locator("div.pre-avl")
        clicked_date = False
        for i in range(date_cells.count()):
            cell_text = date_cells.nth(i).inner_text()
            log(f"Date cell {i}: {cell_text}")
            if "Mar" in cell_text or "Apr" in cell_text:
                date_cells.nth(i).click()
                log(f"✅ Date clicked: {cell_text}")
                clicked_date = True
                break

        if not clicked_date:
            log("⚠️ Date not found — click manually")
            input("Click your journey date then press ENTER...")

        time.sleep(1)

        # Wait for Book Now
        log("⏳ Waiting for Book Now to activate...")
        for wait in range(15):
            btn = page.locator(
                "button.train_Search:has-text('Book Now')"
            )
            if btn.count() > 0:
                log("✅ Book Now is ACTIVE")
                break
            time.sleep(1)
            log(f"Waiting for activation... {wait+1}s")
        else:
            log("⚠️ Book Now not activating")
            input("Click your date then press ENTER...")

        return True

    except Exception as e:
        log(f"❌ Search/select failed: {e}")
        return False

# ============================================
# MODULE 5 — WAIT FOR TATKAL AND BOOK
# ============================================

def wait_and_book(page, book_at, offset=0):
    log("👀 Watching for booking to open...")

    wait_until(book_at, offset)

    for attempt in range(20):
        try:
            btn = page.locator(
                "button.train_Search:has-text('Book Now')"
            )

            if btn.count() > 0:
                log(f"Book Now found: {btn.count()}")
                log(f"Book Now visible: {btn.last.is_visible()}")
                log(f"Book Now enabled: {btn.last.is_enabled()}")

                # Scroll into view
                btn.last.scroll_into_view_if_needed()
                time.sleep(0.5)

                log("🟢 Clicking Book Now — last button")
                btn.last.click()
                time.sleep(3)

                # Check for errors
                if page.locator(
                    "text=Please Try again"
                ).count() > 0:
                    log("❌ Error page")
                    break

                if page.locator(
                    "text=Booking not yet started"
                ).count() > 0:
                    log("⚠️ Too early — retrying")
                    page.evaluate("""
                        var btns = document.querySelectorAll('button');
                        for(var b of btns){
                            if(b.innerText.trim() === 'OK'){
                                b.click();
                                break;
                            }
                        }
                    """)
                    time.sleep(0.5)
                    continue

                # Check passenger form directly
                if page.locator(
                    "input[placeholder='Name']"
                ).count() > 0:
                    log("✅ Passenger form detected")
                    return True

                # Poll URL and form
                for wait in range(20):
                    current = page.url
                    log(f"URL check {wait+1}: {current}")
                    if "psgninput" in current:
                        log("✅ Passenger page reached")
                        return True
                    if "login" in current:
                        log("⚠️ Redirected to login")
                        input("Login and press ENTER...")
                        return True
                    if page.locator(
                        "input[placeholder='Name']"
                    ).count() > 0:
                        log("✅ Passenger form detected in poll")
                        return True
                    time.sleep(1)

                log("⚠️ Continuing anyway")
                return True

        except Exception as e:
            log(f"Retry {attempt}: {e}")

        time.sleep(0.05)

    log("❌ Booking failed")
    return False

# ============================================
# MODULE 6 — FILL PASSENGER FORM
# ============================================

def fill_passengers(page, cfg):
    log("👤 Filling passenger details...")

    try:
        log(f"Current URL: {page.url}")

        # Just wait for passenger form directly
        log("⏳ Waiting for passenger form...")
        page.wait_for_selector(
            "input[placeholder='Name']",
            timeout=60000
        )
        log("✅ Passenger form loaded")

        start = time.time()

        for i, p in enumerate(cfg['passengers']):
            page.locator(
                "input[placeholder='Name']"
            ).nth(i).fill(p['name'])

            page.locator(
                "input[formcontrolname='passengerAge']"
            ).nth(i).fill(p['age'])

            page.locator(
                "select[formcontrolname='passengerGender']"
            ).nth(i).select_option(p['gender'])

            page.locator(
                "select[formcontrolname='passengerBerthChoice']"
            ).nth(i).select_option(p['berth'])

        page.fill("input[id='mobileNumber']", cfg['mobile'])

        elapsed = time.time() - start
        log(f"✅ Passengers filled in {elapsed:.2f}s")

        if cfg.get('test_mode'):
            log("🧪 TEST MODE — stopping before submit")
            log("✅ Full traversal verified!")
            input("Press ENTER to close...")
            return False

        page.click("button:has-text('Continue')")
        log("✅ Continue clicked")
        return True

    except Exception as e:
        log(f"❌ Passenger fill failed: {e}")
        return False

# ============================================
# MODULE 7 — CAPTCHA HANDOFF
# ============================================

def handle_captcha(page):
    log("🔐 Waiting for CAPTCHA...")

    try:
        page.wait_for_selector(
            "img.captcha-img",
            timeout=15000
        )

        beep(3)

        print("\n" + "="*40)
        print("⚠️  CAPTCHA — JUST TYPE NOW!")
        print("    Cursor already in box")
        print("    Press ENTER when done")
        print("="*40 + "\n")

        page.wait_for_url(
            "**/booking/reviewBooking",
            timeout=60000
        )

        log("✅ CAPTCHA solved — SEAT DECIDED!")
        return True

    except Exception as e:
        log(f"❌ CAPTCHA failed: {e}")
        return False

# ============================================
# MODULE 8 — PAYMENT HANDOFF
# ============================================

def handle_payment(page):
    log("💳 Payment page reached")
    beep(2)

    print("\n" + "="*40)
    print("💳 PAYMENT — No hurry!")
    print("   Seat already confirmed/WL")
    print("   Select payment + enter OTP")
    print("="*40 + "\n")

    try:
        page.wait_for_url(
            "**/booking/bookingConfirm**",
            timeout=300000
        )
        log("🎟 BOOKING CONFIRMED!")
        beep(5)
    except:
        log("⏳ Complete payment manually")

# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "="*50)
    print("  QT — Quick Tatkal Agent v1.0")
    print("="*50 + "\n")

    offset = get_ntp_offset()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        page = browser.new_page()

        login(page)

        if not prefill_search(page, config):
            log("❌ Pre-fill failed — exiting")
            browser.close()
            return

        keep_alive(page, config['search_at'], offset)
        wait_until(config['search_at'], offset)

        if not search_and_select(page, config):
            log("❌ Train selection failed — exiting")
            browser.close()
            return

        if not wait_and_book(page, config['book_at'], offset):
            log("❌ Booking failed — exiting")
            browser.close()
            return

        if not fill_passengers(page, config):
            browser.close()
            return

        if not handle_captcha(page):
            browser.close()
            return

        handle_payment(page)

        browser.close()
        log("✅ Agent finished")

if __name__ == "__main__":
    main()