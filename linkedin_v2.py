from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
# from langdetect import detect, LangDetectException
import time
import random
import os
import re
from urllib.parse import urlencode
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


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
        logger.info('driver loaded successfully')
        return driver
    
    def query_url(self):
        query = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"

        params = {}
        params['keywords'] = self.job_title
        params['location'] = self.location
        if "Berlin" in self.location: 
            params['geoId'] = '90009712'
        params['f_TPR'] = f'r{self.time_threshold}'
        params['sortBy'] = 'DD' # or 'R'

        print(f"{query}{urlencode(params)}")
        return f"{query}{urlencode(params)}"

    def get_jobs(self):
        self.driver.get(self.query_url())
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logger.info('Homepage loaded')
        # self.driver.save_screenshot("screenshot2.png")

        job_list = []
        # Find all job cards
        job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.base-card.base-search-card")
        logger.info(f'Found {len(job_cards)} job cards')

        for idx, card in enumerate(job_cards):
            try:
                # Title
                title_elem = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
                title = title_elem.text.strip()

                # Company
                company_elem = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle")
                company = company_elem.text.strip()

                # Location
                location_elem = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location")
                location = location_elem.text.strip()

                # Link
                link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                link = link_elem.get_attribute("href").strip()

                # Time posted
                try:
                    time_elem = card.find_element(By.CSS_SELECTOR, "time.job-search-card__listdate--new")
                except:
                    logger.warning("New job card format detected, trying to find time in old format")
                    time_elem = card.find_element(By.CSS_SELECTOR, "time.job-search-card__listdate")
                time_posted = time_elem.text.strip()


                logger.info(f"Job {idx+1}: {title}, {company}, {location}, {time_posted}, {link}")

                ## Filtering jobs
                if not self.filter_jobs_title(title):
                    logger.info(f"Job {idx+1} filtered out by title: {title}")
                    continue
                if not self.filter_jobs_time(time_posted, self.time_threshold):
                    logger.info(f"Job {idx+1} filtered out by time: {time_posted}")
                    continue

                job_list.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "time_posted": time_posted
                })
                time.sleep(random.uniform(0.5, 1.5))  # Random sleep to avoid detection

            except Exception as e:
                logger.error(f"Error parsing job card {idx+1}: {e}")
                continue

        self.jobs = job_list
        logger.info(f'Jobs extracted: {len(job_list)}')
        return job_list
    
        
    def filter_jobs_resposted(self, time_posted):
        if any(keyword in time_posted for keyword in ["repost", "relist"]):
            return False
        else:
            return True

    def filter_jobs_title(self, title):
        forbidden_list = ["principal", "lead", "head", "manager",
                          "frontend", "backend", "fullstack", "software", "cloud",
                          "security", "java", "javascript", ".net", "legal"]
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

    def close_driver(self):
        self.driver.quit()

        

if __name__ == "__main__":
    linkedin = LinkedIn('Data Science', 'Berlin Metropolitan Area')
    linkedin.get_jobs()
    linkedin.close_driver()
