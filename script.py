import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import json

# load credentials from .env (works locally)
load_dotenv()
USERNAME = os.getenv("ZHS_USER")
PASSWORD = os.getenv("ZHS_PASS")
STREET = os.getenv("STREET")
STREET_NUMBER = os.getenv("STREET_NUMBER")
POSTAL_CODE = os.getenv("POSTAL_CODE")
CITY = os.getenv("CITY")
BIRTHDATE = os.getenv("BIRTHDATE")

COURSE_URL = "https://kurse.zhs-muenchen.de/de/product-offers/37019bf0-24df-4b56-8c6d-2423ea83d30a"

options = Options()
options.add_argument("--headless=new")  # modern headless mode for newer Chrome
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Selenium driver is initialized in main() so startup hangs/errors are visible.
driver = None

import time
from selenium.webdriver.common.keys import Keys

import calendar


def clear_selenium_stale_locks():
    cache_root = Path.home() / ".cache" / "selenium"
    if not cache_root.exists():
        return

    removed = 0
    for lock_file in cache_root.rglob("sm.lock"):
        try:
            lock_file.unlink()
            removed += 1
        except OSError:
            continue

    if removed:
        print(f"Removed {removed} stale Selenium lock file(s).")

def is_five_days_later_target_day():
    target_date = datetime.today() + timedelta(days=5)
    weekday = target_date.weekday()  # Monday=0, Sunday=6

    if weekday in [1, 4, 5]:  # Tuesday, Friday, Saturday
        formatted_date = f"{target_date.day}-{target_date.month}-{target_date.year}"
        print(f"Today is booking day: {formatted_date} for the day {target_date.day}")
        time_key = {1: "Thrs_time", 4: "Fri_time", 5: "Sat_time"}[weekday]
        time_val = os.getenv(time_key)
        if not time_val:
            raise ValueError(f"Missing env var {time_key}. Add it to .env as HH:MM (e.g. 07:59).")
        bk_time = datetime.strptime(time_val, "%H:%M").time()
        
        chose = weekday - 3
        CHOICE_ARRAY = os.getenv("CHOICE", "").split(",")  # Assumes comma-separated values in .env
        CHOICE = CHOICE_ARRAY[chose].strip() if chose < len(CHOICE_ARRAY) else None
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), bk_time) + timedelta(seconds = 60)
    
        if target_datetime < now:
            print(f"Booking time {bk_time} has already passed for today.")
            return False, None, None,None
        else:
            return True, formatted_date, CHOICE, bk_time
        

    else:
        return False, None, None,None



def fill_input_by_id(driver, field_id, value):
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, field_id))
            )

            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, field_id))
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
            input_field.clear()
            input_field.send_keys(value)

            print(f"✅ Filled '{field_id}' with: {value}")
            break

        except StaleElementReferenceException:
            print(f"🔄 Attempt {attempt}/{max_attempts}: stale input field '{field_id}', re-fetching...")
            time.sleep(0.2)

        except Exception as e:
            print(f"⚠️ Attempt {attempt}/{max_attempts} failed to fill '{field_id}': {e}")
            if attempt == max_attempts:
                print(f"❌ All attempts to fill '{field_id}' failed.")
            else:
                time.sleep(0.2)





def main():
    global driver
    try:
        clear_selenium_stale_locks()
        print("Starting Chrome WebDriver...")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        print("Chrome WebDriver started.")
    except Exception as e:
        print(f"Failed to start Chrome WebDriver: {e}")
        return

    valid, bk_date, CHOICE , bk_time = is_five_days_later_target_day()
    
    if not valid :
        #exit the script if today is not the booking day
        #quit_msg = input("Today is not a booking day or the time has passed. Press Enter to exit...")
        print("Today is not a booking day or the time has passed. Exiting...")
        driver.quit()
        return
    # Calculate sleep time until 2 seconds before bk_time
    
    
    try:
        # 1) Open login page (the site may redirect from course -> login)
        driver.get("https://kurse.zhs-muenchen.de/")  # base page

        # 2) Wait & click "Login" if necessary
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
            # First, wait for page to load
                
                
                # Debug: Print page title and check current URL
                print(f"Current URL: {driver.current_url}")
                print(f"Page title: {driver.title}")
                
                # Try to find all links first
                all_links = driver.find_elements(By.TAG_NAME, "a")
                print(f"Total links on page: {len(all_links)}")
                
                # Look for login links
                login_links = [link for link in all_links if '/auth/login' in link.get_attribute('href') if link.get_attribute('href')]
                print(f"Found {len(login_links)} login links")
                
                if login_links:
                    # Try to click the first one found
                    login_link = login_links[0]
                    print(f"Login link href: {login_link.get_attribute('href')}")
                    
                    driver.get(login_link.get_attribute('href'))
                    break
                else:
                    print("No login links found.")
                    break
            except Exception as e:
                print(f"⚠️ Login link not found or clickable, assuming already on login page. Error: {e}")
                if attempt == max_attempts:
                    print("❌ All attempts to click Login link failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying
                # Sometimes there is a login form directly; continue

        
        try:
            # New login UI: open university account dropdown, then choose TUM provider
            university_account_button = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@data-melt-dropdown-menu-trigger and .//span[normalize-space()='Login with University Account']]",
                    )
                )
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", university_account_button)
            driver.execute_script("arguments[0].click();", university_account_button)

            tum_provider_button = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button[type='submit'][form='login-form'][name='provider'][value='oidc-tum']",
                    )
                )
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tum_provider_button)
            driver.execute_script("arguments[0].click();", tum_provider_button)
            print("✅ Selected TUM via university-account dropdown.")
        except Exception as new_ui_error:
            # Legacy fallback: old provider button
            try:
                tum_login_button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.ID, "provider"))
                )
                tum_login_button.click()
                print("✅ Clicked legacy 'provider' login button.")
            except Exception as legacy_error:
                print(
                    f"⚠️ Could not trigger TUM login in new or legacy UI. New UI error: {new_ui_error}; Legacy error: {legacy_error}"
                )

        
        # Fill in username and password
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)

            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys(PASSWORD)

            print("✅ Filled in username and password successfully.")
        except Exception as e:
            print(f"⚠️ Error filling login form: {e}")

        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnLogin"))
            )
            login_button.click()
            print("✅ Submitted the login form successfully.")
        except Exception as e:
            print(f"⚠️ Failed to click the login button: {e}")

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
            # Click the first image with id="poster-0"
                poster_img = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "poster-0"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", poster_img)
                time.sleep(1)
                
                # Remove any overlays that might be intercepting the click
                driver.execute_script("""
                    var overlays = document.querySelectorAll('[role="dialog"], .modal, .overlay, .backdrop, [style*="position: fixed"]');
                    overlays.forEach(el => {
                        if (el.offsetParent !== null) {
                            el.style.display = 'none';
                        }
                    });
                """)
                time.sleep(0.5)
                
                # Try to click using JavaScript to avoid interception
                driver.execute_script("arguments[0].click();", poster_img)
                print("✅ Clicked the first poster image via JavaScript.")
                
                # Wait for page to load after click
                break
            except Exception as e:
                print(f"⚠️ Failed to click first poster image: {e}")
                if attempt == max_attempts:
                    print("❌ All attempts to click poster image failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying

        # Optional: wait for navigation or content to load
            time.sleep(2)

        ## wait unitl bk_time - 2 seconds
        
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), bk_time)
        
        if target_datetime > now:
            sleep_seconds = (target_datetime - now).total_seconds()
            print(f"⏰ Waiting until {target_datetime.strftime('%H:%M:%S')} (sleeping for {sleep_seconds:.1f} seconds)...")
            time.sleep(max(0.0, sleep_seconds - 0.2))
            while datetime.now() < target_datetime:
                pass
            print("✅ Sleep complete, proceeding with booking...")
        else:
            print(f"⚠️ Target time {bk_time} has already passed or is within 2 seconds. Proceeding immediately...")
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # Click the outer <a> tag using its href
                offer_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/de/product-offers/37019bf0-24df-4b56-8c6d-2423ea83d30a')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", offer_link)
                driver.execute_script("arguments[0].click();", offer_link)
                print("✅ Clicked the offer link successfully.")
                break  # Exit loop on success
            except Exception as e:
                print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click offer link: {e}")
                if attempt == max_attempts:
                    print("❌ All attempts to click offer link failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying

        """ max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                testid = f"product-tabs-trigger-{CHOICE}"
                if not testid:
                    raise ValueError(f"Invalid CHOICE value: {CHOICE}")

                button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"button[data-testid='{testid}']"))
                )

                # Scroll and click using JS to avoid interception
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                driver.execute_script("arguments[0].click();", button)
                
                print(f"✅ Clicked button {CHOICE} successfully.")
                break  # Exit loop on success
            except Exception as e:
                print(f"⚠️ Attempt {attempt}/{max_attempts} failed for button {CHOICE}: {e}")
                if attempt == max_attempts:
                    print(f"❌ All attempts to click button {CHOICE} failed.")
                    print(f"testid: {testid}")
                else:
                    time.sleep(0.1)  # Wait before retrying
             """
        testid = "date-picker-0-trigger"
        max_attempts = 5
        trigger_opened = False
        for attempt in range(1, max_attempts + 1):
            print(f"Testid for calendar trigger: {testid}")
            try:
                # Re-locate the element inside the try block to avoid stale reference
                trigger = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{testid}']"))
                )

                # Scroll and click via JS
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                driver.execute_script("arguments[0].click();", trigger)

                # In headless mode the click may happen but not open immediately; confirm expanded state.
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, f"button[data-testid='{testid}']").get_attribute("aria-expanded") == "true"
                )

                print("✅ Clicked the calendar trigger button.")
                trigger_opened = True
                break  # Exit loop on success

            except StaleElementReferenceException:
                print(f"🔄 Attempt {attempt}/{max_attempts}: stale element, re-fetching...")
                time.sleep(0.2)  # Give DOM time to settle

            except Exception as e:
                print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click calendar trigger {testid}: {e}")
                if attempt == max_attempts:
                    print(f"❌ All attempts to click calendar trigger button failed.")
                else:
                    time.sleep(0.2)

        calendar_ready = False
        if trigger_opened:
            for open_attempt in range(1, 4):
                try:
                    # Some headless runs don't expose the old content testid; check visible day cells directly.
                    WebDriverWait(driver, 6).until(
                        lambda d: len(
                            [
                                el
                                for el in d.find_elements(By.CSS_SELECTOR, "button[data-value][data-melt-calendar-cell]")
                                if el.is_displayed()
                            ]
                        )
                        > 0
                    )
                    print(f"✅ Calendar day cells are visible (attempt {open_attempt}/3).")
                    calendar_ready = True
                    break
                except Exception as e:
                    print(f"⚠️ Calendar day cells not visible (attempt {open_attempt}/3): {e}")
                    if open_attempt < 3:
                        try:
                            trigger = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{testid}']"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                            driver.execute_script("arguments[0].click();", trigger)
                            WebDriverWait(driver, 3).until(
                                lambda d: d.find_element(By.CSS_SELECTOR, f"button[data-testid='{testid}']").get_attribute("aria-expanded")
                                == "true"
                            )
                            time.sleep(0.2)
                        except Exception as reopen_error:
                            print(f"⚠️ Failed to reopen calendar on retry: {reopen_error}")
        else:
            print("❌ Calendar trigger did not open; date selection will likely fail.")

        target_date = datetime.strptime(bk_date, "%d-%m-%Y")
        target_testid = f"date-picker-0-calendar-day-{bk_date}"
        target_data_value = target_date.strftime("%Y-%m-%dT00:00:00")
        target_aria_label = (
            f"{target_date.strftime('%A')}, {target_date.strftime('%B')} {target_date.day}, {target_date.year}"
        )

        print(f"Target calendar date testid: {target_testid}")
        print(f"Target calendar date data-value: {target_data_value}")
        print(f"Target calendar date aria-label: {target_aria_label}")

        candidate_selectors = [
            ("data-testid", By.CSS_SELECTOR, f"button[data-testid='{target_testid}']"),
            ("data-value", By.CSS_SELECTOR, f"button[data-value='{target_data_value}']"),
            ("data-value-prefix", By.CSS_SELECTOR, f"button[data-value^='{target_date.strftime('%Y-%m-%d')}']"),
            ("aria-label", By.CSS_SELECTOR, f"button[aria-label=\"{target_aria_label}\"]"),
        ]

        clicked_date = False
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            if not calendar_ready:
                try:
                    WebDriverWait(driver, 4).until(
                        lambda d: len(
                            [
                                el
                                for el in d.find_elements(By.CSS_SELECTOR, "button[data-value][data-melt-calendar-cell]")
                                if el.is_displayed()
                            ]
                        )
                        > 0
                    )
                    calendar_ready = True
                except Exception:
                    pass

            for selector_name, by, selector in candidate_selectors:
                try:
                    date_btn = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_btn)
                    driver.execute_script("arguments[0].click();", date_btn)
                    print(f"✅ Clicked calendar date button via {selector_name}: {selector}")
                    clicked_date = True
                    break
                except Exception:
                    continue

            if clicked_date:
                break

            print(
                f"⚠️ Attempt {attempt}/{max_attempts} failed to click calendar date button with all selectors."
            )
            if attempt < max_attempts:
                try:
                    # Re-open calendar between date attempts in headless mode.
                    trigger = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{testid}']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                    driver.execute_script("arguments[0].click();", trigger)
                    time.sleep(0.2)
                except Exception:
                    pass
                time.sleep(0.1)

        if not clicked_date:
            print(
                "❌ All attempts to click calendar date button failed for data-testid, data-value, and aria-label. "
                "Not navigating to next month by design."
            )
        time.sleep(0.1)  # Small delay to allow slots to start loading
        disabled = True
        slot_selector = "//button[starts-with(@data-testid, 'slot-list-0-slot')]"
        print(f"slot xpath: {slot_selector}")

        slot_wait_deadline = time.time() + 60
        while time.time() < slot_wait_deadline:
            try:
                slot_buttons = driver.find_elements(By.XPATH, slot_selector)

                if not slot_buttons:
                    time.sleep(0.3)
                    continue

                enabled_slot = None
                disabled_count = 0

                for candidate in slot_buttons:
                    try:
                        if candidate.get_attribute("disabled") is None:
                            enabled_slot = candidate
                            break
                        disabled_count += 1
                    except StaleElementReferenceException:
                        continue

                if enabled_slot is not None:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", enabled_slot)
                    driver.execute_script("arguments[0].click();", enabled_slot)
                    print("🖱️ Clicked an ENABLED slot from slot-list-0.")
                    disabled = False
                    break

                print(
                    f"⏳ Found {len(slot_buttons)} slot-list-0 slot(s), all disabled ({disabled_count}). Waiting for enable..."
                )
                time.sleep(0.4)

            except Exception as e:
                error_text = str(e).lower()
                if "invalid session id" in error_text or "session deleted" in error_text:
                    print("❌ Browser session ended during slot polling. Stopping retries.")
                    break
                print(f"⚠️ Slot polling error: {e}")
                time.sleep(0.2)

        if disabled:
            print("❌ No enabled slot found in slot-list-0 within 60 seconds.")

        if not disabled:
            max_attempts = 3

            for attempt in range(1, max_attempts + 1):
                try:
                    # Re-locate the save button each time to avoid stale reference
                    save_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='save-button']"))
                    )
                    button_text1 = save_button.text.strip()
                    print(f"🕵️ Button text: '{button_text1}'")

                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='save-button']"))
                    )

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button)
                    driver.execute_script("arguments[0].click();", save_button)

                    print("✅ Clicked 'In den Warenkorb' save button.")
                    break

                except StaleElementReferenceException:
                    print(f"🔄 Attempt {attempt}/{max_attempts}: stale save button, re-fetching...")
                    time.sleep(0.2)

                except Exception as e:
                    print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click save button: {e}")
                    if attempt == max_attempts:
                        print("❌ All attempts to click save button failed.")
                    else:
                        time.sleep(0.2)
            max_attempts = 3

            for attempt in range(1, max_attempts + 1):
                try:
                    save_button2 = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='save-button']"))
                    )
                    button_text2 = save_button2.text.strip()
                    print(f"🕵️ Initial button text: '{button_text2}'")

                    # Wait for button text to change
                    timeout = 20  # seconds
                    start_time = time.time()

                    while button_text1 == button_text2:
                        if time.time() - start_time > timeout:
                            print("❌ Timeout: Button text did not change.")
                            break

                        try:
                            save_button2 = driver.find_element(By.CSS_SELECTOR, "button[data-testid='save-button']")
                            button_text2 = save_button2.text.strip()
                            print(f"🔄 Still same text: '{button_text2}'")
                        except Exception as e:
                            print(f"⚠️ Error while checking button text: {e}")

                        time.sleep(0.5)  # Polling delay

                    print("✅ Button text has changed, re-fetching clickable state...")
                    
                    save_button2 = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='save-button']"))
                    )
                    
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='save-button']"))
                    )

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", save_button2)
                    driver.execute_script("arguments[0].click();", save_button2)

                    print("✅ Clicked '{button_text2}' save button.")
                    break

                except StaleElementReferenceException:
                    print(f"🔄 Attempt {attempt}/{max_attempts}: stale save button, re-fetching...")
                    time.sleep(0.2)

                except Exception as e:
                    print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click save button: {e}")
                    if attempt == max_attempts:
                        print("❌ All attempts to click save button failed.")
                    else:
                        time.sleep(0.2)

            fill_input_by_id(driver, "street_name", STREET)
            fill_input_by_id(driver, "street_number", STREET_NUMBER)
            fill_input_by_id(driver, "postal_code", POSTAL_CODE)
            fill_input_by_id(driver, "city", CITY)
            fill_input_by_id(driver, "birthdate", BIRTHDATE)
            
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    # Re-locate the button fresh each time to avoid stale reference
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='submit-user-form-button']"))
                    )

                    # Wait until it's clickable
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='submit-user-form-button']"))
                    )

                    # Scroll and click via JS
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                    driver.execute_script("arguments[0].click();", submit_button)

                    print("✅ Clicked 'Further' submit button.")
                    break  # Exit loop on success

                except StaleElementReferenceException:
                    print(f"🔄 Attempt {attempt}/{max_attempts}: stale element, re-fetching...")
                    time.sleep(0.2)

                except Exception as e:
                    print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click submit button: {e}")
                    if attempt == max_attempts:
                        print("❌ All attempts to click submit button failed.")
                    else:
                        time.sleep(0.2)

                
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    checkbox = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "condition_acceptance"))
                    )

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)

                    if not checkbox.is_selected():
                        checkbox.click()
                        print("✅ Checkbox 'condition_acceptance' has been ticked.")
                    else:
                        print("ℹ️ Checkbox 'condition_acceptance' was already ticked.")
                    break

                except StaleElementReferenceException:
                    print(f"🔄 Attempt {attempt}/{max_attempts}: stale checkbox, re-fetching...")
                    time.sleep(0.2)

                except Exception as e:
                    print(f"⚠️ Attempt {attempt}/{max_attempts} failed to tick checkbox: {e}")
                    if attempt == max_attempts:
                        print("❌ All attempts to tick checkbox failed.")
                    else:
                        time.sleep(0.2)

            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    consent_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='submit-consent-form-button']"))
                    )

                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='submit-consent-form-button']"))
                    )

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", consent_button)
                    driver.execute_script("arguments[0].click();", consent_button)

                    print("✅ Clicked 'Book for a fee' button.")
                    break

                except StaleElementReferenceException:
                    print(f"🔄 Attempt {attempt}/{max_attempts}: stale button, re-fetching...")
                    time.sleep(0.2)

                except Exception as e:
                    print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click 'Book for a fee': {e}")
                    if attempt == max_attempts:
                        print("❌ All attempts to click 'Book for a fee' button failed.")
                    else:
                        time.sleep(0.2)
            
            time.sleep(1)
            success_url = "https://kurse.zhs-muenchen.de/booking/result-pages/success"
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    WebDriverWait(driver, 10).until(EC.url_contains("/booking/result-pages/success"))
                    print(f"✅ Reached success page: {driver.current_url}")
                    if driver.current_url.startswith(success_url):
                        print("✅ Booking success confirmed.")
                    else:
                        print("ℹ️ Redirected but URL differs, current:", driver.current_url)

                    # Check for the thank-you text on the success page
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//font[contains(normalize-space(.), 'Thank you for your booking!')]")
                            )
                        )
                        print("✅ Found confirmation text 'Thank you for your booking!'.")
                    except TimeoutException:
                        print("❌ Confirmation text not found on success page.")
                except TimeoutException:
                    print(f"❌ Did not reach success page within timeout. Current URL: {driver.current_url}")
                    if attempt == max_attempts:
                        print("❌ All attempts to reach success page failed.")
                    else:
                        time.sleep(0.2)
            
            


        time.sleep(2)                        
        print("✅ Script finished — browser will stay open until you press Enter.")
        #input("Press Enter here to close the browser...")

    finally:
        """ cookies = driver.get_cookies()
        with open("zhs_cookies.json", "w") as f:
            json.dump(cookies, f) """
        print("Saved cookies to zhs_cookies.json")
        # Keep browser open for inspection if you want; otherwise quit:
        if driver is not None:
            driver.quit() 





if __name__ == "__main__":
    main()

