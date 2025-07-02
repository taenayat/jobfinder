from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from langdetect import detect, LangDetectException
import time
import random
import os
import re

class LinkedIn:
    def __init__(self, job_title, location, time_threshold=3600):
        self.job_title = job_title
        self.location = location
        self.driver = self.init_driver()
        self.actions = ActionChains(self.driver)
        self.time_threshold = time_threshold


    def init_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver_path = ChromeDriverManager().install()
        driver_dir = os.path.dirname(driver_path)
        actual_driver_path = os.path.join(driver_dir, "chromedriver")
        if not os.path.exists(actual_driver_path):
            actual_driver_path = driver_path
        service = Service(executable_path=actual_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        print('driver loaded successfully')
        return driver
    
    def get_jobs(self):

        self.driver.get("https://www.linkedin.com/jobs/search/")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print('homepage loaded')

        # Sign-in pop-up
        try:
            self._close_signin_popup()
            print('sign-in pop-up closed')
        except Exception as e:
            print("Sign-in pop-up not detected; continuing with job extraction.")
        # -------------------

        # Input job title
        title_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search job titles or companies']"))
        )
        title_input.send_keys(self.job_title)
        self._random_delay()

        # Input location
        location_input = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label='Location']")
        location_input.clear()  # Clear existing text
        location_input.send_keys(self.location)
        self._random_delay()

        # Press Enter
        location_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Wait for job results to load
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
        )
        self._random_delay()
        print('jobs loaded')
        
        self.driver.save_screenshot("screenshot1.png")
        # Apply filter for "Last 24 hours"
        try:
            self._last_24_hours_filter()
            self._random_delay()
            print('applied last 24 hours filter')
        except Exception as e:
            print("Failed to apply 'Last 24 hours' filter:", e)


        # Scroll to load all jobs (adjust iterations as needed)
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._random_delay()

        # Find all job listings
        self.jobs = self.driver.find_elements(By.CLASS_NAME, "base-card")
        self._random_delay()
        print('jobs listed, total:', len(self.jobs))
        return self.jobs
    
    def click(self, button):
        self.actions.move_to_element(button).pause(random.uniform(1, 2)).click().perform()

    def _random_delay(self):
        time.sleep(random.uniform(2, 5))
    
    def _close_signin_popup(self):
        WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in to view more jobs')]")
            )
        )
        close_button = self.driver.find_element(By.XPATH, '//*[@id="base-contextual-sign-in-modal"]/div/section/button')
        self.click(close_button)
        # close_button.click()
        time.sleep(1)

    
    def _last_24_hours_filter(self):
        date_posted_filter = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Date posted filter. Any time filter is currently applied. Clicking this button displays all Date posted filter options.']"))
        )
        self.click(date_posted_filter)
        self._random_delay()
        # date_posted_filter.click()

        last_24_hours_option = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id='f_TPR-3']"))
        )
        self.click(last_24_hours_option)
        self._random_delay()
        # last_24_hours_option.click()
        done = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class='filter__submit-button']"))
        )
        self.click(done)
        # done.click()
        time.sleep(3)

    def _get_job_description(self, job_element):
        # self.driver.get(job_link)
        self.click(job_element)
        self._random_delay()
        description = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "description__text"))
        ).text
        actual_time_posted = WebDriverWait(self.driver, 10).until(
            # EC.presence_of_element_located(((By.XPATH, ".//*[contains(@class, posted-time-ago)]")))
            EC.presence_of_element_located(((By.CSS_SELECTOR, "span.posted-time-ago__text")))
        ).text.strip().lower()
        return description, actual_time_posted

    def _is_english(self, text):
        try:
            return detect(text) == 'en'
        except LangDetectException:
            return False
        
    def filter_jobs_resposted(self, time_posted):
        if any(keyword in time_posted for keyword in ["repost", "relist"]):
            return False
        else:
            return True

    def filter_jobs_title(self, title):
        forbidden_list = ["software", "principal", "lead", "head", "manager"]
        necessary_list = ["data"]
        title = title.lower()
        for item in forbidden_list:
            if item in title:
                return False
        return True


    def parse_time(self, time_str):
        time_str = time_str.strip().lower()
        pattern = r"(\d+) (second|minute|hour|day|week|year)s? ago"
        match = re.match(pattern, time_str)
        
        if not match:
            raise ValueError("Invalid time format")
        
        number = int(match.group(1))
        unit = match.group(2)
        
        time_units = {
            'second': 1,
            'minute': 60,
            'hour': 60 * 60,
            'day': 24 * 60 * 60,
            'week': 7 * 24 * 60 * 60,
            'year': 365 * 24 * 60 * 60
        }
        if unit not in time_units:
            raise ValueError(f"Unsupported time unit: {unit}")
        return number * time_units[unit]

    def filter_jobs_time(self, time_posted, time_threshold):
        time_in_seconds = self.parse_time(time_posted)
        if time_in_seconds <= time_threshold:
            return True
        else:
            return False


    def get_data_from_jobs(self):
        job_list = []
        for idx, job in enumerate(self.jobs):
            try:
                title = job.find_element(By.CLASS_NAME, "base-search-card__title").text.strip()
                company = job.find_element(By.CLASS_NAME, "base-search-card__subtitle").text.strip()
                location = job.find_element(By.CLASS_NAME, "job-search-card__location").text.strip()
                link = job.find_element(By.TAG_NAME, "a").get_attribute("href").strip()
                time_posted = job.find_element(By.XPATH, ".//*[contains(@class, 'job-search-card__listdate')]").text.strip()
                self._random_delay()
                print(f"{title}, {company}, {location}, {time_posted}, {link}")

                if not self.filter_jobs_title(title):
                    print('title filter')
                    continue
                if not self.filter_jobs_time(time_posted, self.time_threshold):
                    print('time filter')
                    continue
                description, actual_time_posted = self._get_job_description(job)
                if not self.filter_jobs_resposted(actual_time_posted):
                    print('repost')
                    continue
                if not self._is_english(description):
                    print('language filter')
                    continue

                job_list.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "time_posted": time_posted
                })
                print(f"\nJob {idx+1}:")
                print(f"Title: {title}")
                print(f"Company: {company}")
                print(f"Location: {location}")
                print(f"Time Posted: {time_posted}")
                print(f"Link: {link}")
            except Exception as e:
                print(e)
                continue
        print('data from jobs extracted')
        return job_list

    def close_driver(self):
        self.driver.quit()

    def show_jobs(self):
        self.get_jobs()
        job_list = self.get_data_from_jobs()
        print(job_list)
        self.close_driver()

        

if __name__ == "__main__":
    linkedin = LinkedIn('Data Science', 'Berlin Metropolitan Area')
    linkedin.show_jobs()




# def parse_time(time_str):
#     time_str = time_str.strip().lower()
#     pattern = r"(\d+) (second|minute|hour|day|week|year)s? ago"
#     match = re.match(pattern, time_str)
    
#     if not match:
#         raise ValueError("Invalid time format")
    
#     number = int(match.group(1))
#     unit = match.group(2)
    
#     time_units = {
#         'second': 1,
#         'minute': 60,
#         'hour': 60 * 60,
#         'day': 24 * 60 * 60,
#         'week': 7 * 24 * 60 * 60,
#         'year': 365 * 24 * 60 * 60
#     }
#     if unit not in time_units:
#         raise ValueError(f"Unsupported time unit: {unit}")
#     return number * time_units[unit]

# def filter_jobs_title(title):
#     forbidden_list = ["software", "principal", "lead", "head"]
#     necessary_list = ["data"]
#     title = title.lower()
#     for item in forbidden_list:
#         if item in title:
#             return False
#     return True
# title = 'Head of Artificial Intelligence Go-To-Market, Google Cloud'
# print(filter_jobs_title(title))
# time_str = '4 hours ago'
# print(parse_time(time_str))





# def linkedin_job_search(driver, job_title, location):

#     # Open LinkedIn Jobs page
#     driver.get("https://www.linkedin.com/jobs/search/")
#     # Wait for initial page load
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.TAG_NAME, "body"))
#     )

#     # ---- Handle the "Sign in to view more jobs" pop-up ----
#     try:
#         # Wait a short time to see if the pop-up appears
#         sign_in_popup = WebDriverWait(driver, 3).until(
#             EC.presence_of_element_located(
#                 (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in to view more jobs')]")
#             )
#         )
#         # Once detected, try to locate and click the close/dismiss button
#         # close_button = driver.find_element(By.CSS_SELECTOR, "button.artdeco-modal__dismiss")
#         close_button = driver.find_element(By.XPATH, '//*[@id="base-contextual-sign-in-modal"]/div/section/button')
        
#         close_button.click()
#         # Wait a moment for the modal to disappear
#         time.sleep(1)
#     except Exception as e:
#         # If the pop-up isn't present, just continue
#         print("Sign-in pop-up not detected; continuing with job extraction.")
#     # ---------------------------------------------------------

#     # Input job title
#     title_input = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search job titles or companies']"))
#     )
#     title_input.send_keys(job_title)

#     # Input location
#     location_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Location']")
#     location_input.clear()  # Clear existing text
#     location_input.send_keys(location)
#     # location_input.click()

#     # Click search button
#     # search_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Search']")
#     # search_button.click()

#     # Click on first location to search
#     # first_location_suggestion = WebDriverWait(driver, 10).until(
#     #     EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='listbox'] li"))
#     # )
#     # first_location_suggestion.click()

#     # Press Enter
#     location_input.send_keys(Keys.RETURN)
#     time.sleep(2)

#     # print(driver.current_url)
#     # time.sleep(1)
#     # driver.save_screenshot("screenshot1.png")

#     # Wait for job results to load
#     WebDriverWait(driver, 20).until(
#         EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
#     )
    

#     # Apply filter for "Last 24 hours"
#     try:
#         # Open the "Date Posted" filter dropdown
#         date_posted_filter = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Date posted filter. Any time filter is currently applied. Clicking this button displays all Date posted filter options.']"))
#         )
#         date_posted_filter.click()

#         # Select "Last 24 hours"
#         last_24_hours_option = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id='f_TPR-3']"))
#         )
#         last_24_hours_option.click()

#         # Click Done
#         done = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class='filter__submit-button']"))
#         )
#         done.click()

#         # Wait for the filter to be applied
#         time.sleep(3)  # Adjust sleep time as needed
#     except Exception as e:
#         print("Failed to apply 'Last 24 hours' filter:", e)

#     # Scroll to load all jobs (adjust iterations as needed)
#     for _ in range(3):
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(1)

#     # driver.save_screenshot("screenshot1.png")
    
#     # Find all job listings
#     jobs = driver.find_elements(By.CLASS_NAME, "base-card")

#     return jobs

# def job_data_extraction(jobs):
#     job_list = []
#     for job in jobs:
#         try:
#             title = job.find_element(By.CLASS_NAME, "base-search-card__title").text.strip()
#             company = job.find_element(By.CLASS_NAME, "base-search-card__subtitle").text.strip()
#             location = job.find_element(By.CLASS_NAME, "job-search-card__location").text.strip()
#             link = job.find_element(By.TAG_NAME, "a").get_attribute("href").strip()
#             time_posted = job.find_element(By.XPATH, ".//*[contains(@class, 'job-search-card__listdate')]").text.strip()
            
#             job_list.append({
#                 "title": title,
#                 "company": company,
#                 "location": location,
#                 "link": link,
#                 "time_posted": time_posted
#             })

#         except Exception as e:
#             continue

#     return job_list

# if __name__ == "__main__":
#     # job_title = input("Enter job title: ")
#     # location = input("Enter location: ")
#     job_title = "Data Scientist"
#     location = "Berlin Metropolitan Area"

#     # Set up the driver
#     options = Options()
#     options.add_argument('--headless')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')

#     driver_path = ChromeDriverManager().install()
#     driver_dir = os.path.dirname(driver_path)
#     actual_driver_path = os.path.join(driver_dir, "chromedriver")
#     if not os.path.exists(actual_driver_path):
#         actual_driver_path = driver_path
#     service = Service(executable_path=actual_driver_path)
#     driver = webdriver.Chrome(service=service, options=options)
#     driver.maximize_window() 
    
#     try:
#         jobs = linkedin_job_search(driver, job_title, location)
#         # jobs_extracted = job_data_extraction(jobs)

#     except:
#         jobs_extracted = [{"title": 0, "company": 0, "location": 0, "link": 0, "time_posted": 0}]
#         print("Problem Loading Jobs")
#     # finally:
#     #     driver.quit()
#     jobs_extracted = job_data_extraction(jobs)

    
#     print(f"\nFound {len(jobs_extracted)} jobs:")
#     for idx, job in enumerate(jobs_extracted, 1):
#         print(f"\nJob {idx}:")
#         print(f"Title: {job['title']}")
#         print(f"Company: {job['company']}")
#         print(f"Location: {job['location']}")
#         print(f"Time Posted: {job['time_posted']}")
#         print(f"Link: {job['link']}")

