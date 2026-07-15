import os
from google.oauth2.service_account import Credentials
from googleapiclient import discovery

CREDENTIALS_PATH = r"C:\Users\topor\Downloads\drink_tracker_bot\drink_tracker_bot\credentials.json"
SPREADSHEET_ID = "1z1yW3c4wd36Ognk2zhKDsHb2zs6dXi194FKJmU9lo0w"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def main():
    credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    service = discovery.build('sheets', 'v4', credentials=credentials)
    
    rows_to_add = [
        [
            "09.07.2026",
            "Lipton Тропический (Манго и Личи)",
            1000,
            "-",
            190,
            45,
            0,
            0,
            "Бутылка 1л (газированный)"
        ],
        [
            "13.07.2026",
            "Добрый Cola",
            1000,
            "-",
            420,
            106,
            130,
            100,
            "Бутылка 1л"
        ],
        [
            "13.07.2026",
            "Evervess Cola",
            1500,
            "-",
            645,
            162,
            195,
            150,
            "Бутылка 1.5л"
        ]
    ]

    body = {
        "values": rows_to_add
    }

    try:
        # Use append method to add rows to the end of the data in the sheet
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Покупки!A:I",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"Успешно добавлено строк: {result.get('updates').get('updatedRows')}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
