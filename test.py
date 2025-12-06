import os
import time
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
options.add_argument("--headless")  # headless mode for GitHub runner
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Selenium Manager will fetch the right driver automatically
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

import time
from selenium.webdriver.common.keys import Keys

import calendar

def is_five_days_later_target_day():
    target_date = datetime.today() + timedelta(days=5)
    weekday = target_date.weekday()  # Monday=0, Sunday=6

    if weekday in [3, 4, 5]:  # Thursday, Friday, Saturday
        formatted_date = f"{target_date.day}-{target_date.month}-{target_date.year}"
        print(f"Today is booking day: {formatted_date} for the day {target_date.day}")
        time_key = {3: "Thrs_time", 4: "Fri_time", 5: "Sat_time"}[weekday]
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
        try:
            login_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/auth/login')]"))
            )
            login_link.click()
            print("✅ Clicked the 'Login' button successfully.")
        except Exception:
            print("⚠️ Login link not found or clickable, assuming already on login page.")
            # Sometimes there is a login form directly; continue
            pass
        
        try:
            # Wait for the button with id="provider" and click it
            tum_login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "provider"))
            )
            tum_login_button.click()
            print("✅ Clicked the 'Login with TUM account' button successfully.")
        except Exception:
            print("⚠️ TUM login button not found or not clickable.")

        
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

        try:
        # Click the first image with id="poster-0"
            poster_img = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "poster-0"))
            )
            poster_img.click()
            print("✅ Clicked the first poster image.")
        except Exception as e:
            print(f"⚠️ Failed to click first poster image: {e}")

        # Optional: wait for navigation or content to load
            time.sleep(2)

        ## wait unitl bk_time - 2 seconds
        
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), bk_time)
        
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

        max_attempts = 3
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
            
        testid = f"date-picker-{CHOICE}-trigger"
        if not testid:
            raise ValueError(f"Invalid CHOICE value: {CHOICE}")
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            print(f"Testid for calendar trigger: {testid}")
            try:
                # Re-locate the element inside the try block to avoid stale reference
                trigger = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"button[data-testid='{testid}']"))
                )

                # Wait until it's clickable
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{testid}']"))
                )

                # Scroll and click via JS
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                driver.execute_script("arguments[0].click();", trigger)

                print(f"✅ Clicked the calendar trigger button for choice {CHOICE}.")
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

         
       # ...existing code...
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # Wait for the calendar container to appear
                cal_container_testid = f"date-picker-{CHOICE}-content"
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='{cal_container_testid}']")))
                print("✅ Calendar container appeared.")
                break  # Exit loop on success
            except Exception as e:
                print(f"⚠️ Attempt {attempt}/{max_attempts} failed - Calendar container did not appear: {e}")
                if attempt == max_attempts:
                    print("❌ All attempts to find calendar container failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying
       
        target_testid = f"date-picker-{CHOICE}-calendar-day-{bk_date.replace('-', '-')}"
        target_selector = f"button[data-testid='{target_testid}']"
        current_date = datetime.now()
        m = current_date.month
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:    
                if m != datetime.now().month:
                    print(f"Date button {target_testid} not found, navigating months...")
                    next_btn_testid = f"date-picker-{CHOICE}-calendar-next-button"
                    next_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{next_btn_testid}']")))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                    driver.execute_script("arguments[0].click();", next_btn)
                    print("✅ Clicked next month button.")
                    break
                else:
                    date_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{target_testid}']"))
                    )
                    print(f"✅ Date button {target_testid} found, no need to navigate months.")
                    break               
            except Exception as e:
                print(f"⚠️ Failed clicking next month button: {e}")
                if attempt == max_attempts:
                    print("❌ All attempts to find calendar container failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying
                    
                    
        date_button_testid = f"date-picker-{CHOICE}-calendar-day-{bk_date.replace('-', '-')}"       
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:  
                date_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-testid='{date_button_testid}']"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_btn)
                driver.execute_script("arguments[0].click();", date_btn)
                print(f"✅ Clicked calendar date button {date_button_testid}.")
                break  # Exit loop on success
            except Exception as e:
                print(f"⚠️ Attempt {attempt}/{max_attempts} failed to click calendar date button: {e}")
                if attempt == max_attempts:
                    print("❌ All attempts to click calendar date button failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying
        time.sleep(0.1)  # Small delay to allow slots to load
        disabled = True 
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                slot_selector = f"//button[starts-with(@data-testid, 'slot-list-{CHOICE}-slot')]"
                print(f"slot xpath: {slot_selector}")

                # Wait up to 10 seconds for the element to be present in the DOM and visible
                wait = WebDriverWait(driver, 10)
                slot_button = wait.until(EC.visibility_of_element_located((By.XPATH, slot_selector)))

                if slot_button.get_attribute("disabled") is not None:
                    print(f"⚠️ Slot button for CHOICE={CHOICE} is present but DISABLED.")
                    disabled = True
                    break  # Exit loop if disabled
                else:
                    print(f"✅ Slot button for CHOICE={CHOICE} is present and ENABLED.")
                    # Scroll into view and click via JS to avoid interception
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", slot_button)
                    driver.execute_script("arguments[0].click();", slot_button)
                    print(f"🖱️ Clicked slot button for CHOICE={CHOICE}.")
                    disabled = False
                    break  # Exit loop on success

            except TimeoutException:
                print(f"⏳ Timeout: Slot button for CHOICE={CHOICE} did not appear within 10 seconds.")
                if attempt == max_attempts:
                    print(f"❌ All attempts to process slot button for CHOICE={CHOICE} failed.")
            except Exception as e:
                print(f"⚠️ Attempt {attempt}/{max_attempts} failed while processing slot button for CHOICE={CHOICE}: {e}")
                if attempt == max_attempts:
                    print(f"❌ All attempts to process slot button for CHOICE={CHOICE} failed.")
                else:
                    time.sleep(0.1)  # Wait before retrying

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


    


                                
        print("✅ Script finished — browser will stay open until you press Enter.")
        #input("Press Enter here to close the browser...")

    finally:
        cookies = driver.get_cookies()
        with open("zhs_cookies.json", "w") as f:
            json.dump(cookies, f)
        print("Saved cookies to zhs_cookies.json")
        # Keep browser open for inspection if you want; otherwise quit:
        driver.quit() 





if __name__ == "__main__":
    main()

