import pandas as pd
import numpy as np
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json

logger = logging.getLogger(__name__)

class GoogleSheets:
    def __init__(self, credentials_info, spreadsheet_id, sheet_name):
        self.credentials_info = credentials_info
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        creds = service_account.Credentials.from_service_account_info(
            self.credentials_info,
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
        
        # print(f"✅ Appended row to {self.sheet_name}")
        return result


class DataStorage:
    def __init__(self, filename='jobs_data.csv', use_csv=True, use_google_sheets=False, 
                 credentials_info=None, spreadsheet_id=None, worksheet_name=None):
        self.filename = filename
        self.use_csv = use_csv
        self.use_google_sheets = use_google_sheets
        self.credentials_info = credentials_info
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name

        if self.use_google_sheets:
            if not all([self.credentials_info, self.spreadsheet_id, self.worksheet_name]):
                logger.error("For Google Sheets storage, credentials_info, spreadsheet_id, and worksheet_name must be provided.")
                raise ValueError("For Google Sheets storage, credentials_info, spreadsheet_id, and worksheet_name must be provided.")

            try:
                self.sheets = GoogleSheets(self.credentials_info, self.spreadsheet_id, self.worksheet_name)
            except Exception as e:
                logger.error(f"Google Sheets loading error: {e}")
                logger.info(f"Falling back to CSV file: {self.filename}")
                self.use_csv = True
                self.use_google_sheets = False


    def save_job(self, job_list):
        if self.use_csv:
            if not os.path.exists(self.filename):
                header = pd.DataFrame(columns=['timestamp', 'job_title', 'company', 'location', 'link'])
                header.to_csv(self.filename, index=False)
                logger.warning(f"File {self.filename} does not exist. Starting with an empty DataFrame.")

            new_row = pd.DataFrame([job_list])
            new_row.to_csv(self.filename, mode='a', header=False, index=False)
            logger.info(f"New job added to {self.filename}")

        if self.use_google_sheets:
            self.sheets.append_row(job_list)
            logger.info(f"New job added to spreadsheet {self.worksheet_name} (with spreadsheet ID of {self.spreadsheet_id}).")


if __name__ == "__main__":
    load_dotenv()

    job_data = {
        'timestamp': '2025-09-25 10:45:39',
        'job_title': 'Data Scientist',
        'company': 'Big Company',
        'location': 'Berlin',
        'link': 'www.bigcompany.com'
    }
    storage = DataStorage(use_csv=True, use_google_sheets=True, credentials_info=json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON')),
        spreadsheet_id=os.getenv('SPREADSHEET_ID'),
        worksheet_name=os.getenv('WORKSHEET_NAME'))
    # storage = DataStorage(use_csv=True)
    storage.save_job(list(job_data.values()))
