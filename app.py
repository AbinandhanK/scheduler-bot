from flask import Flask, request
import requests
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz
import dateparser
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
app = Flask(__name__)

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    response = requests.post(url, data=data)
    print("Sent message:", response.text)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Received data:", data)

    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')

    if chat_id is None or text == '':
        print("No message or chat_id found.")
        return 'ok'

    if text.startswith('/add_event'):
        try:
            parts = text.split(' ', 3)
            print("DEBUG: parts =", parts)
            if len(parts) < 4:
                send_message(chat_id, "❌ Usage: /add_event YYYY-MM-DD HH:MM Event title")
                return 'ok'

            date_str, time_str, title = parts[1], parts[2], parts[3]

            event_datetime = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            event_body = {
                'summary': title,
                'start': {'dateTime': event_datetime.isoformat(), 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': (event_datetime + datetime.timedelta(hours=1)).isoformat(), 'timeZone': 'Asia/Kolkata'},
            }

            creds = Credentials.from_authorized_user_file('token.json')
            service = build('calendar', 'v3', credentials=creds)
            service.events().insert(calendarId='primary', body=event_body).execute()
            send_message(chat_id, f"Event added to your calendar: {title} at {event_datetime.strftime('%I:%M %p on %B %d, %Y')} 👍")
        except Exception as e:
            print("Error:", e)
            send_message(chat_id, "Failed to add event.⚠️ Use format:\n/add_event 2025-06-18 18:00 Call with mentor")
        return 'ok'

    if chat_id is None or text == '':
        print("No message or chat_id found.")
        return '', 200

    print(f"User said: {text}")

    if text.startswith('/start'):
        send_message(chat_id, "Vankkam! I'm your calendar bot. Send /help to see what I can do.")
    elif text.startswith('/help'):
        send_message(chat_id, "You can use commands like:\n/add_event - to add to calendar\n/show_events - to list your schedule")
    elif text.startswith('/show_events'):
        try:
            creds = Credentials.from_authorized_user_file('token.json')
            service = build('calendar', 'v3', credentials=creds)

            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' = UTC time
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            if not events:
                send_message(chat_id, "No upcoming events found.📭")
                return 'ok'

            response_text = "📅 Upcoming Events:\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                local_time = datetime.datetime.fromisoformat(start).astimezone().strftime("%d %b %Y, %I:%M %p")
                response_text += f"• {local_time} - {event['summary']}\n"

            send_message(chat_id, response_text)

        except Exception as e:
            print("Error fetching events ⚠️:", e)
            send_message(chat_id, "Failed to fetch events. ⚠️")

    else:
        send_message(chat_id, f"You said: {text}")

    return '', 200

if __name__ == '__main__':
    app.run(debug=True)

