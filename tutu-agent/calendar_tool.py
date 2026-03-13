"""
Google Calendar integration â Imani's hands for time management.
Uses a service account for authentication.
"""
import os
import json
from datetime import datetime, timedelta

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS", "")
TUTU_CALENDAR_ID = os.getenv("TUTU_CALENDAR_ID", "primary")


class CalendarManager:
    def __init__(self):
        self.service = None
        self._init_service()

    def _init_service(self):
        """Initialize Google Calendar API service."""
        if not GOOGLE_CREDENTIALS:
            return

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_dict = json.loads(GOOGLE_CREDENTIALS)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

            # If using domain-wide delegation, impersonate Tutu
            tutu_email = os.getenv("TUTU_EMAIL", "")
            if tutu_email:
                creds = creds.with_subject(tutu_email)

            self.service = build("calendar", "v3", credentials=creds)
        except Exception as e:
            print(f"Google Calendar not configured: {e}")
            self.service = None

    def is_connected(self) -> bool:
        return self.service is not None

    def get_events(self, date_str: str = None, days: int = 1) -> dict:
        """Get events for a specific date or date range.

        Args:
            date_str: Date in YYYY-MM-DD format. Defaults to today.
            days: Number of days to look ahead from date_str.

        Returns:
            Dict with 'success' bool and 'events' list or 'error' string.
        """
        if not self.service:
            return {"success": False, "error": "Google Calendar not connected. Ask Tutu to set up GOOGLE_CREDENTIALS on Railway."}

        try:
            if date_str:
                start_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            end_date = start_date + timedelta(days=days)

            time_min = start_date.isoformat() + "Z"
            time_max = end_date.isoformat() + "Z"

            events_result = self.service.events().list(
                calendarId=TUTU_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = events_result.get("items", [])
            formatted = []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                formatted.append({
                    "id": event.get("id", ""),
                    "title": event.get("summary", "(No title)"),
                    "start": start,
                    "end": end,
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "status": event.get("status", "confirmed"),
                })

            return {"success": True, "events": formatted, "date": date_str or "today", "days": days}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_event(
        self,
        title: str,
        date: str,
        start_time: str = None,
        end_time: str = None,
        description: str = "",
        location: str = "",
        all_day: bool = False,
    ) -> dict:
        """Create a calendar event.

        Args:
            title: Event title/summary.
            date: Date in YYYY-MM-DD format.
            start_time: Start time in HH:MM format (24h). Required if not all_day.
            end_time: End time in HH:MM format (24h). Required if not all_day.
            description: Optional event description.
            location: Optional location.
            all_day: If True, creates an all-day event.

        Returns:
            Dict with 'success' bool and 'event' dict or 'error' string.
        """
        if not self.service:
            return {"success": False, "error": "Google Calendar not connected. Ask Tutu to set up GOOGLE_CREDENTIALS on Railway."}

        try:
            if all_day:
                event_body = {
                    "summary": title,
                    "start": {"date": date},
                    "end": {"date": date},
                    "description": description,
                    "location": location,
                }
            else:
                if not start_time or not end_time:
                    return {"success": False, "error": "start_time and end_time are required for non-all-day events"}

                # Build datetime strings with timezone
                tz = os.getenv("TUTU_TIMEZONE", "Africa/Lagos")
                start_dt = f"{date}T{start_time}:00"
                end_dt = f"{date}T{end_time}:00"

                event_body = {
                    "summary": title,
                    "start": {"dateTime": start_dt, "timeZone": tz},
                    "end": {"dateTime": end_dt, "timeZone": tz},
                    "description": description,
                    "location": location,
                }

            event = self.service.events().insert(
                calendarId=TUTU_CALENDAR_ID,
                body=event_body,
            ).execute()

            return {
                "success": True,
                "event": {
                    "id": event.get("id"),
                    "title": event.get("summary"),
                    "link": event.get("htmlLink"),
                    "start": event["start"].get("dateTime", event["start"].get("date")),
                    "end": event["end"].get("dateTime", event["end"].get("date")),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_event(self, event_id: str, updates: dict) -> dict:
        """Update an existing calendar event.

        Args:
            event_id: The event ID to update.
            updates: Dict of fields to update (title, start_time, end_time, description, location).

        Returns:
            Dict with 'success' bool and updated 'event' or 'error'.
        """
        if not self.service:
            return {"success": False, "error": "Google Calendar not connected."}

        try:
            event = self.service.events().get(
                calendarId=TUTU_CALENDAR_ID, eventId=event_id
            ).execute()

            if "title" in updates:
                event["summary"] = updates["title"]
            if "description" in updates:
                event["description"] = updates["description"]
            if "location" in updates:
                event["location"] = updates["location"]

            updated = self.service.events().update(
                calendarId=TUTU_CALENDAR_ID, eventId=event_id, body=event
            ).execute()

            return {
                "success": True,
                "event": {
                    "id": updated.get("id"),
                    "title": updated.get("summary"),
                    "link": updated.get("htmlLink"),
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_event(self, event_id: str) -> dict:
        """Delete a calendar event.

        Args:
            event_id: The event ID to delete.

        Returns:
            Dict with 'success' bool.
        """
        if not self.service:
            return {"success": False, "error": "Google Calendar not connected."}

        try:
            self.service.events().delete(
                calendarId=TUTU_CALENDAR_ID, eventId=event_id
            ).execute()
            return {"success": True, "message": "Event deleted."}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_free_slots(self, date_str: str, duration_minutes: int = 60) -> dict:
        """Find available time slots on a given date.

        Args:
            date_str: Date in YYYY-MM-DD format.
            duration_minutes: Minimum slot duration in minutes.

        Returns:
            Dict with 'success' and 'slots' list.
        """
        if not self.service:
            return {"success": False, "error": "Google Calendar not connected."}

        try:
            result = self.get_events(date_str, days=1)
            if not result["success"]:
                return result

            events = result["events"]

            # Define working hours (9 AM to 8 PM)
            work_start = 9 * 60  # minutes from midnight
            work_end = 20 * 60

            busy = []
            for evt in events:
                start = evt["start"]
                end = evt["end"]
                # Parse times to minutes
                if "T" in start:
                    s_hour, s_min = int(start[11:13]), int(start[14:16])
                    e_hour, e_min = int(end[11:13]), int(end[14:16])
                    busy.append((s_hour * 60 + s_min, e_hour * 60 + e_min))

            busy.sort()

            # Find gaps
            free_slots = []
            current = work_start
            for start, end in busy:
                if start - current >= duration_minutes:
                    free_slots.append({
                        "start": f"{current // 60:02d}:{current % 60:02d}",
                        "end": f"{start // 60:02d}:{start % 60:02d}",
                        "duration_minutes": start - current,
                    })
                current = max(current, end)

            if work_end - current >= duration_minutes:
                free_slots.append({
                    "start": f"{current // 60:02d}:{current % 60:02d}",
                    "end": f"{work_end // 60:02d}:{work_end % 60:02d}",
                    "duration_minutes": work_end - current,
                })

            return {"success": True, "date": date_str, "free_slots": free_slots}

        except Exception as e:
            return {"success": False, "error": str(e)}
     try:
            result = self.get_events(date_str, days=1)
            if not result["success"]:
                return result

            events = result["events"]

            # Define working hours (9 AM to 8 PM)
            work_start = 9 * 60  # minutes from midnight
            work_end = 20 * 60

            busy = []
            for evt in events:
                start = evt["start"]
                end = evt["end"]
                # Parse times to minutes
                if "T" in start:
                    s_hour, s_min = int(start[11:13]), int(start[14:16])
                    e_hour, e_min = int(end[11:13]), int(end[14:16])
                    busy.append((s_hour * 60 + s_min, e_hour * 60 + e_min))

            busy.sort()

            # Find gaps
            free_slots = []
            current = work_start
            for start, end in busy:
                if start - current >= duration_minutes:
                    free_slots.append({
                        "start": f"{current // 60:02d}:{current % 60:02d}",
                        "end": f"{start // 60:02d}:{start % 60:02d}",
                        "duration_minutes": start - current,
                    })
                current = max(current, end)

            if work_end - current >= duration_minutes:
                free_slots.append({
                    "start": f"{current // 60:02d}:{current % 60:02d}",
                    "end": f"{work_end // 60:02d}:{work_end % 60:02d}",
                    "duration_minutes": work_end - current,
                })

            return {"success": True, "date": date_str, "free_slots": free_slots}

        except Exception as e:
            return {"success": False, "error": str(e)}

