import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


logger = logging.getLogger(__name__)

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self):
        self.creds_json_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID')

        if not self.creds_json_str or not self.calendar_id:
            raise ValueError("Google Calendar credentials or ID not set in environment.")
        
        try:
            # Load credentials from the JSON string
            creds_info = json.loads(self.creds_json_str)
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=self.SCOPES)
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("GoogleCalendarService initialized successfully.")
        except json.JSONDecodeError:
            logger.error("Failed to parse GOOGLE_CREDENTIALS_JSON. Please ensure it is a valid JSON string.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            raise

    def create_event(self, summary: str, description: str, start_time: datetime, duration_minutes: int = 30, timezone: str = 'UTC'):
        try:
            # Ensure start_time is timezone-aware or convert to specified timezone
            if start_time.tzinfo is None:
                from datetime import timezone as dt_timezone
                start_time = start_time.replace(tzinfo=dt_timezone.utc)

            end_time = start_time + timedelta(minutes=duration_minutes)

            event = {
                'summary': f'Appointment: {summary}',
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
            }

            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            logger.info(f"Event created: {created_event.get('htmlLink')}")
            return created_event.get('id')

        except HttpError as e:
            logger.error(f"HTTP error creating Google Calendar event: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating Google Calendar event: {e}")
            return None
    
    def delete_event(self, event_id: str):
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Event {event_id} deleted successfully.")
            return True
        except HttpError as e:
            logger.error(f"HTTP error deleting Google Calendar event {event_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting Google Calendar event {event_id}: {e}")
            return False
            
    def list_calendars(self):
        """List all accessible calendars to verify access."""
        try:
            calendars = self.service.calendarList().list().execute()
            calendar_list = [cal['id'] for cal in calendars.get('items', [])]
            logger.info(f"Accessible calendars: {calendar_list}")
            return calendar_list
        except Exception as e:
            logger.error(f"Error listing calendars: {e}")
            return []