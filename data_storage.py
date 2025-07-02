import pandas as pd
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataStorage:
    def __init__(self, filename='jobs_data.csv'):
        self.filename = filename

    def load_data(self):
        if os.path.exists(self.filename):
            self.data = pd.read_csv(self.filename)
        else:
            self.data = pd.DataFrame(columns=['timestamp', 'job_title', 'company', 'location', 'link'])
            logger.warning(f"File {self.filename} does not exist. Starting with an empty DataFrame.")

    def get_data(self):
        return self.data

    def save_data(self):
        self.data.to_csv(self.filename, index=False)

    def add_job(self, timestamp, job_title, company, location, link):
        new_job = {
            'timestamp': timestamp,
            'job_title': job_title,
            'company': company,
            'location': location,
            'link': link
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_job])], ignore_index=True)

if __name__ == "__main__":
    storage = DataStorage()
    storage.load_data()
    # Example of adding a job
    storage.add_job(pd.Timestamp.now(), 'Software Engineer', 'Tech Company', 'Berlin', 'https://example.com/job1')
    storage.save_data()
    print(storage.get_data())