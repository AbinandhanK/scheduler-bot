from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the old token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    creds = None

    # Load existing token if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid token available, request login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Test the credentials
    service = build('calendar', 'v3', credentials=creds)
    calendar_list = service.calendarList().list().execute()

    print("✅ Successfully authenticated! Calendars:")
    for calendar in calendar_list['items']:
        print(f"- {calendar['summary']}")

if __name__ == '__main__':
    main()
