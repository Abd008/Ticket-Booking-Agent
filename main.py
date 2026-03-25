# -*- coding: utf-8 -*-
# main.py
# QT — Quick Tatkal Agent v1.0
# Author: Abd008

from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import pytz
import ntplib
from datetime import datetime
import winsound
import json
import sys

# ============================================
# CONFIGURATION
# ============================================

config = {
    "from_station": "SBC",
    "to_station":   "TLG",
    "date":         "25/03/2026",
    "quota":        "GENERAL",
    "train_number": "16227",
    "travel_class": "SL",

    "passengers": [
        {
            "name":   "Abhishek Bharadwaj",
            "age":    "20",
            "gender": "M",
            "berth":  "SU",
        }
    ],

    "mobile": "8660713011",

    "search_at": {"hour": 0, "min": 0, "sec": 0},
    "book_at":   {"hour": 0, "min": 0, "sec": 5},

    "test_mode": False,
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
    line = f"[{now}] {msg}"

    print(line)

    # write to log file
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ============================================
# HUMAN-LIKE BEHAVIOR FUNCTIONS
# ============================================

def human_delay(min_ms=500, max_ms=2000):
    """Random delay to mimic human reaction time"""
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)

def human_move_and_click(page, locator):
    """Move mouse to element before clicking (human-like behavior)"""
    human_delay(300, 800)
    locator.scroll_into_view_if_needed()
    human_delay(100, 300)
    locator.click()

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
        # ✅ DEFENSIVE: Ensure required fields exist
        from_station = cfg.get('from_station', '').strip().upper()
        to_station = cfg.get('to_station', '').strip().upper()
        quota = cfg.get('quota', '').strip()
        date = cfg.get('date', '').strip()
        
        if not from_station or not to_station or not quota or not date:
            log(f"❌ Missing required fields: from={from_station}, to={to_station}, quota={quota}, date={date}")
            return False

        # ✅ FUNCTION: Select from autocomplete with retry
        def select_from_autocomplete(input_locator, station_code, input_label):
            log(f"🔍 Selecting {input_label}: {station_code}")
            input_locator.click()
            time.sleep(0.5)
            input_locator.fill("")
            input_locator.type(station_code[:3])  # Type first 3 chars
            time.sleep(2)

            options = page.locator("li.ui-autocomplete-list-item")
            log(f"Options found for {input_label}: {options.count()}")
            
            selected = False
            for i in range(options.count()):
                text = options.nth(i).inner_text()
                log(f"  Option {i}: {text}")
                
                # Match by station code at the beginning or in first line
                if station_code in text.upper():
                    options.nth(i).click(force=True)
                    log(f"✅ Clicked: {text}")
                    time.sleep(1)
                    selected = True
                    break
            
            if not selected:
                log(f"⚠️ {input_label} option not found for {station_code}")
                # Press escape to close dropdown
                page.keyboard.press("Escape")
                time.sleep(0.5)
            
            # Verify the value was committed
            final_value = input_locator.input_value()
            log(f"✅ {input_label} final value: '{final_value}'")
            return selected

        # Select From Station
        from_input = page.locator(
            "input[aria-label='Enter From station. Input is Mandatory.']"
        )
        select_from_autocomplete(from_input, from_station, "From Station")
        time.sleep(1)

        # Select To Station
        to_input = page.locator(
            "input[aria-label='Enter To station. Input is Mandatory.']"
        )
        select_from_autocomplete(to_input, to_station, "To Station")
        time.sleep(1)

        from_val = from_input.input_value()
        to_val = to_input.input_value()
        log(f"From filled: {from_val}")
        log(f"To filled: {to_val}")

        # Select Date
        date_input = page.locator("input.ui-inputtext").nth(2)
        date_input.click()
        time.sleep(0.5)
        date_input.press("Control+a")
        date_input.type(date)
        time.sleep(0.5)
        page.keyboard.press("Escape")
        time.sleep(0.5)

        # Select Quota
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
            if quota in text:
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
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
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

                btn.last.scroll_into_view_if_needed()
                time.sleep(0.5)

                log("🟢 Clicking Book Now — last button")
                btn.last.click()
                time.sleep(3)

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

                if page.locator(
                    "input[placeholder='Name']"
                ).count() > 0:
                    log("✅ Passenger form detected")
                    return True

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
# MODULE 6 — PASSENGER FORM → REVIEW PAGE
# ============================================

def fill_passengers(page, cfg):

    log("👤 Filling passenger details...")

    try:
        log(f"Current URL: {page.url}")

        # ==========================
        # WAIT FOR FORM
        # ==========================
        page.wait_for_selector("input[placeholder='Name']", timeout=60000)
        log("✅ Passenger form loaded")

        start = time.time()

        # ==========================
        # PASSENGER FILL (WITH ANGULAR DELAY)
        # ==========================
        for i, p in enumerate(cfg['passengers']):
            log(f"👤 Passenger {i+1}: {p['name']}")
            
            # Name field
            name_input = page.locator("input[placeholder='Name']").nth(i)
            name_input.click()
            human_delay(200, 400)
            name_input.fill(p["name"])
            human_delay(300, 600)  # Wait for Angular validation
            name_input.blur()
            human_delay(200, 400)

            # Age field
            age_input = page.locator(
                "input[formcontrolname='passengerAge']"
            ).nth(i)
            age_input.click()
            human_delay(200, 400)
            age_input.fill(p["age"])
            human_delay(300, 600)
            age_input.blur()
            human_delay(200, 400)

            # Gender field
            gender_select = page.locator(
                "select[formcontrolname='passengerGender']"
            ).nth(i)
            gender_select.click()
            human_delay(100, 300)
            gender_select.select_option(p["gender"])
            human_delay(300, 500)
            gender_select.blur()
            human_delay(200, 400)

            # Berth field
            berth_select = page.locator(
                "select[formcontrolname='passengerBerthChoice']"
            ).nth(i)
            berth_select.click()
            human_delay(100, 300)
            berth_select.select_option(p["berth"])
            human_delay(300, 500)
            berth_select.blur()
            human_delay(200, 400)
            
            log(f"✅ Passenger {i+1} filled")

        # Mobile - with longer delay
        log("📱 Filling mobile number...")
        mobile_input = page.locator("input#mobileNumber")
        mobile_input.click()
        human_delay(200, 400)
        mobile_input.fill(cfg["mobile"])
        human_delay(400, 800)  # Longer wait for mobile validation
        mobile_input.blur()
        human_delay(300, 500)

        elapsed = time.time() - start
        log(f"✅ Form filled in {elapsed:.2f}s")

        # ==========================
        # PAYMENT MODE (UPI) — BEFORE CONTINUE
        # ==========================
        log("💳 Selecting payment mode (UPI) on this form...")

        try:
            payment_mode = str(cfg.get("payment_mode", "")).strip().lower()
            
            if payment_mode in ["upi", "bhim", "bhim/upi"]:
                log("🔎 Looking for UPI/BHIM payment option...")
                human_delay(300, 600)
                
                # Try to find payment section on this form
                try:
                    page.wait_for_selector("text=Payment Mode", timeout=5000)
                    log("✅ Payment Mode section visible")
                    human_delay(500, 1000)
                    
                    # First, see what payment options exist
                    page.evaluate("""
                        () => {
                            const radios = document.querySelectorAll("input[type='radio'][name='paymentType']");
                            console.log('Found ' + radios.length + ' payment radio buttons');
                            for (let i = 0; i < radios.length; i++) {
                                const label = radios[i].closest("label, tr");
                                console.log('Radio ' + i + ': ' + (label ? label.innerText.substring(0, 50) : 'no label'));
                            }
                        }
                    """)
                    
                    # Click the UPI radio button - SPECIFICALLY "BHIM/UPI" option
                    upi_found = page.evaluate("""
                        () => {
                            const radios = document.querySelectorAll("input[type='radio'][name='paymentType']");
                            console.log('Searching for BHIM/UPI among ' + radios.length + ' options');
                            
                            for (let i = 0; i < radios.length; i++) {
                                const radio = radios[i];
                                const container = radio.closest("tr") || radio.closest("label") || radio.closest("div");
                                if (container) {
                                    const text = container.innerText.toUpperCase();
                                    console.log('Radio ' + i + ' value=' + radio.value + ' text: ' + text.substring(0, 60));
                                    
                                    // Look SPECIFICALLY for "BHIM/UPI" or "BHIM" or "PAY THROUGH BHIM"
                                    // NOT "UPI_CC" or "UPI_CL"
                                    const hasBHIM = text.includes('BHIM');
                                    const isPureUPI = text.includes('PAY THROUGH BHIM') || (text.includes('/UPI') && !text.includes('UPI_'));
                                    
                                    if (hasBHIM || isPureUPI) {
                                        console.log('Found BHIM/UPI match! Radio ' + i + ' with value: ' + radio.value);
                                        console.log('Before click - checked: ' + radio.checked);
                                        
                                        radio.click();
                                        radio.checked = true;
                                        radio.dispatchEvent(new Event('change', { bubbles: true }));
                                        radio.dispatchEvent(new Event('click', { bubbles: true }));
                                        
                                        // Verify immediately
                                        console.log('After click - radio.checked: ' + radio.checked);
                                        
                                        return {
                                            success: true,
                                            radioIndex: i,
                                            radioValue: radio.value,
                                            isChecked: radio.checked,
                                            containerText: text.substring(0, 100)
                                        };
                                    }
                                }
                            }
                            console.log('Pure BHIM/UPI option NOT found');
                            return {
                                success: false,
                                reason: 'Dedicated BHIM/UPI option not found (found UPI_CC/UPI_CL but that is not pure BHIM)'
                            };
                        }
                    """)
                    
                    log(f"UPI Click Result: {upi_found}")
                    
                    if upi_found.get('success'):
                        radio_info = f"Radio #{upi_found.get('radioIndex')} (value={upi_found.get('radioValue')})"
                        is_checked = upi_found.get('isChecked')
                        container_text = upi_found.get('containerText', '')
                        
                        log(f"✅ Clicked {radio_info}")
                        log(f"   Text: {container_text}")
                        log(f"   Checked: {is_checked}")
                        
                        if is_checked:
                            log("✅ UPI/BHIM selected successfully (VERIFIED)")
                        else:
                            log("⚠️ Radio clicked but NOT checked")
                        
                        human_delay(800, 1500)
                    else:
                        reason = upi_found.get('reason', 'unknown')
                        log(f"⚠️ {reason}")
                        log("❌ Pure BHIM/UPI option not found")
                        log("⚠️ Manual UPI selection required...")
                        input("MANUAL: Please click BHIM/UPI radio button and press ENTER")
                    
                except Exception as e:
                    log(f"⚠️ Payment mode search error: {e}")
                    input("MANUAL: Please select UPI/BHIM and press ENTER")
            else:
                log(f"ℹ️ Payment mode '{payment_mode}' not UPI — skipping")
        
        except Exception as e:
            log(f"❌ Payment mode selection error: {e}")

        human_delay(500, 1000)

        # ==========================
        # CONTINUE BUTTON (CAUTIOUS APPROACH)
        # ==========================
        log("⏳ Waiting for Angular form validation...")

        # Wait for Angular to mark form as valid
        page.wait_for_function("""
            () => {
                const btn = [...document.querySelectorAll("button")]
                    .find(b => b.innerText.trim() === "Continue");
                if (!btn) return false;
                // Check if button is enabled (not disabled)
                return !btn.disabled;
            }
        """, timeout=30000)

        log("✅ Continue button is now enabled")
        human_delay(500, 1000)  # Wait a bit more for safety

        # Extra wait to ensure Angular has finished all validations
        page.wait_for_timeout(1000)

        # ==========================
        # INSURANCE (OPTIONAL) — BEFORE CONTINUE
        # ==========================
        log("⏳ Checking for insurance section...")

        try:
            page.wait_for_selector(
                "label:has-text(\"No, I don't want travel insurance\")",
                timeout=3000
            )

            log("✅ Insurance section detected")

            no_insurance = page.locator(
                "label:has-text(\"No, I don't want travel insurance\")"
            )

            # Click to decline insurance
            for attempt in range(3):
                try:
                    no_insurance.first.click(timeout=2000)
                    log("✅ Insurance declined")
                    human_delay(300, 600)
                    break
                except:
                    if attempt < 2:
                        log(f"⚠️ Insurance click failed, retry {attempt+1}/3")
                        human_delay(200, 400)

        except:
            log("ℹ️ Insurance not present on form — skipping")

        human_delay(500, 1000)

        # ==========================
        # CLICK CONTINUE BUTTON
        # ==========================
        continue_btn = page.locator(
            "button:has-text('Continue')"
        ).first

        # Verify button is visible and enabled
        if continue_btn.is_visible() and continue_btn.is_enabled():
            log("🖱 Clicking Continue button...")
            human_delay(200, 500)
            continue_btn.click()
            log("✅ Continue clicked")
            human_delay(1000, 2000)  # Wait for page transition
        else:
            log("⚠️ Continue button not ready, using alternative click")
            page.evaluate("""
                () => {
                    let btn = [...document.querySelectorAll("button")]
                        .find(b => b.innerText.trim() === "Continue");
                    if (btn && !btn.disabled) {
                        btn.click();
                    }
                }
            """)
            log("✅ Continue clicked (JS fallback)")
            human_delay(1000, 2000)

        return True

    except Exception as e:
        log(f"❌ Passenger fill failed: {e}")

        try:
            page.screenshot(path="passenger_error.png")
            log("📸 Screenshot saved")
        except:
            pass

        return False

# ============================================
# MODULE 7 — CAPTCHA HANDOFF
# ============================================

def handle_captcha(page):

    log("🔐 CAPTCHA stage reached")

    try:
        # Wait for ANY captcha indicator (robust detection)
        page.wait_for_function("""
            () => {
                return (
                    document.querySelector("input[placeholder*='Captcha']") ||
                    document.querySelector("input[formcontrolname*='captcha']") ||
                    document.querySelector("img[src*='captcha']") ||
                    document.querySelector("canvas") ||
                    document.body.innerText.toLowerCase().includes("captcha")
                );
            }
        """, timeout=60000)

        log("✅ CAPTCHA detected")

        beep(3)

        print("\n========================================")
        print("⚠️ CAPTCHA — TYPE NOW")
        print("After typing press ENTER in terminal")
        print("========================================")

        # Try focusing input box
        try:
            page.locator(
                "input[placeholder*='Captcha'], input[formcontrolname*='captcha']"
            ).first.click(timeout=2000)
        except:
            pass

        input("Press ENTER after solving captcha...")

        log("✅ CAPTCHA entered")

        return True

    except Exception as e:

        log(f"❌ CAPTCHA detection failed: {e}")

        try:
            page.screenshot(path="captcha_error.png")
            log("📸 Screenshot saved: captcha_error.png")
        except:
            pass

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

# clear previous logs
open("logs.txt", "w").close()
def main():
    print("\n" + "="*50)
    print("  QT — Quick Tatkal Agent v1.0")
    print("="*50 + "\n")

    # ✅ READ CONFIG FROM FLASK WHEN AVAILABLE
    global config
    if len(sys.argv) > 1:
        try:
            flask_config = json.loads(sys.argv[1])
            config.update(flask_config)
            log(f"📥 Config loaded from Flask: payment_mode={config.get('payment_mode')}, quota={config.get('quota')}")
        except Exception as e:
            log(f"⚠️ Failed to load config from Flask: {e}")
    
    # ✅ ENSURE ALL CRITICAL FIELDS HAVE VALUES
    required_fields = {
        'from_station': 'SBC',
        'to_station': 'TLG',
        'date': '25/03/2026',
        'quota': 'GENERAL',
        'train_number': '16227',
        'travel_class': 'SL',
        'mobile': '8660713011',
        'payment_mode': 'upi'
    }
    for field, default in required_fields.items():
        if not config.get(field):
            config[field] = default
            log(f"⚠️ Using default for {field}: {default}")

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

        try:
            print("\nAutomation finished.")
            input("Press ENTER to close browser...")

        finally:
            try:
                browser.close()
            except:
                pass

        log("✅ Agent finished")

if __name__ == "__main__":
    main()