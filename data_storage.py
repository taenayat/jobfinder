import pandas as pd
import numpy as np
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleSheets:
    def __init__(self, credentials_file, spreadsheet_id, sheet_name):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_file, 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=creds)
    
    def append_row(self, data_list):
        """Appends a row to the specified worksheet"""
        body = {
            'values': [data_list]
        }
        
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.sheet_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"✅ Appended row to {self.sheet_name}")
        return result
    
    def append_rows(self, data_lists):
        """Appends multiple rows to the specified worksheet"""
        body = {
            'values': data_lists
        }
        
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.sheet_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"✅ Appended {len(data_lists)} rows to {self.sheet_name}")
        return result


class DataStorage:
    def __init__(self, filename='jobs_data.csv', use_csv=True, use_google_sheets=False, 
                 credentials_file=None, spreadsheet_id=None, worksheet_name=None):
        self.filename = filename
        self.use_csv = use_csv
        self.use_google_sheets = use_google_sheets
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name

        if self.use_google_sheets:
            if not all([self.credentials_file, self.spreadsheet_id, self.worksheet_name]):
                raise ValueError("For Google Sheets storage, credentials_file, spreadsheet_id, and worksheet_name must be provided.")
            self.sheets = GoogleSheets(self.credentials_file, self.spreadsheet_id, self.worksheet_name)

    def save_job(self, job_dict):
        if self.use_csv:
            if not os.path.exists(self.filename):
                header = pd.DataFrame(columns=['timestamp', 'job_title', 'company', 'location', 'link'])
                header.to_csv(self.filename, index=False)
            job_dict.to_csv(self.filename, mode='a', header=False, index=False)
        if self.use_google_sheets:
            self.sheets.append_row(job_dict)



    def load_data(self):
        if self.use_csv:
            if os.path.exists(self.filename):
                self.csv_data = pd.read_csv(self.filename)
            else:
                self.csv_data = pd.DataFrame(columns=['timestamp', 'job_title', 'company', 'location', 'link'])
                logger.warning(f"File {self.filename} does not exist. Starting with an empty DataFrame.")

    def get_data(self):
        return self.data

    def save_data(self, data):
        if self.use_csv and self.csv_data is not None:
            data.to_csv(self.filename, index=False)
            logger.info(f"Data saved to CSV file: {self.filename}")

        if self.use_google_sheets:
            self.sheets.append_row(self.data)
            logger.info(f"Data saved to {self.worksheet_name} Spreadsheet!")

    def add_job(self, timestamp, job_title, company, location, link):
        new_job = {
            'timestamp': timestamp,
            'job_title': job_title,
            'company': company,
            'location': location,
            'link': link
        }
        if self.use_csv:
            self.data = pd.concat([self.data, pd.DataFrame([new_job])], ignore_index=True)
        if self.use_google_sheets:
            self.data = new_job.values()

if __name__ == "__main__":
    storage = DataStorage()
    storage.load_data()
    # Example of adding a job
    storage.add_job(pd.Timestamp.now(), 'Software Engineer', 'Tech Company', 'Berlin', 'https://example.com/job1')
    storage.save_data()
    print(storage.get_data())