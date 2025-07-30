from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

# Check if token file exists
if not os.path.exists('token.json'):
    print("❌ token.json not found.")
    exit()

try:
    # Load credentials
    creds = Credentials.from_authorized_user_file('token.json')

    # Try accessing Google Calendar API
    service = build('calendar', 'v3', credentials=creds)
    calendar_list = service.calendarList().list().execute()

    print("✅ token.json is valid.")
    print("Calendars found:")
    for calendar in calendar_list.get('items', []):
        print(f"- {calendar['summary']}")

except Exception as e:
    print("❌ token.json is invalid or expired.")
    print("Error:", e)
