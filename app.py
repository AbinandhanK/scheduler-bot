from flask import Flask, request
import requests
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz
from dotenv import load_dotenv
import os
import traceback

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

app = Flask(__name__)

# Send message to Telegram user
def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    response = requests.post(url, data=data)
    print("✅ Sent message:", response.text)

# Main webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("🔔 Incoming Telegram data:", data)

    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')

    if not chat_id or not text:
        print("⚠️ No chat_id or message text found.")
        return 'ok'

    print(f"📩 User said: {text}")

    # Handle /start command
    if text.startswith('/start'):
        send_message(chat_id, "Vannakkam! I'm your calendar bot. Use /help to see what I can do.")
        return 'ok'

    # Handle /help command
    if text.startswith('/help'):
        send_message(chat_id, "You can use:\n/add_event YYYY-MM-DD HH:MM Title\n/show_events to list upcoming events.")
        return 'ok'

    # Handle /add_event
    if text.startswith('/add_event'):
        try:
            parts = text.split(' ', 3)
            print("🔍 Parsed parts:", parts)

            if len(parts) < 4:
                send_message(chat_id, "❌ Usage: /add_event YYYY-MM-DD HH:MM Event Title")
                return 'ok'

            date_str, time_str, title = parts[1], parts[2], parts[3]

            # Create datetime in Asia/Kolkata timezone
            tz = pytz.timezone("Asia/Kolkata")
            event_datetime = tz.localize(datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))

            event_body = {
                'summary': title,
                'start': {'dateTime': event_datetime.isoformat(), 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': (event_datetime + datetime.timedelta(hours=1)).isoformat(), 'timeZone': 'Asia/Kolkata'},
            }

            creds = Credentials.from_authorized_user_file('token.json')
            service = build('calendar', 'v3', credentials=creds)
            service.events().insert(calendarId='primary', body=event_body).execute()

            readable_time = event_datetime.strftime('%I:%M %p on %B %d, %Y')
            send_message(chat_id, f"✅ Event added: '{title}' at {readable_time}")
        except Exception as e:
            print("❌ Error occurred while adding event:")
            traceback.print_exc()
            send_message(chat_id, f"⚠️ Failed to add event. Reason: {e}")
        return 'ok'

    # Handle /show_events
    if text.startswith('/show_events'):
        try:
            creds = Credentials.from_authorized_user_file('token.json')
            service = build('calendar', 'v3', credentials=creds)

            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            if not events:
                send_message(chat_id, "📭 No upcoming events found.")
                return 'ok'

            response = "📅 Upcoming Events:\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                local_time = datetime.datetime.fromisoformat(start).astimezone().strftime("%d %b %Y, %I:%M %p")
                response += f"• {local_time} - {event['summary']}\n"

            send_message(chat_id, response)
        except Exception as e:
            print("❌ Error fetching events:")
            traceback.print_exc()
            send_message(chat_id, "⚠️ Could not fetch events. Try again.")
        return 'ok'

    # Default response
    send_message(chat_id, f"You said: {text}")
    return 'ok'

# Start Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

