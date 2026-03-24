"""
Google Sheets integration — reads/writes to Tutu's tracker and calendar.
Uses a service account for authentication.
"""
import os
import json
from datetime import datetime

# Google Sheets setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TRACKER_SHEET_ID = os.getenv("TRACKER_SHEET_ID", "")
CALENDAR_SHEET_ID = os.getenv("CALENDAR_SHEET_ID", "")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS", "")


class SheetsManager:
    def __init__(self):
        self.service = None
        self._init_service()

    def _init_service(self):
        """Initialize Google Sheets API service."""
        if not GOOGLE_CREDENTIALS:
            return

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_dict = json.loads(GOOGLE_CREDENTIALS)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            self.service = build("sheets", "v4", credentials=creds)
        except Exception as e:
            print(f"Google Sheets not configured: {e}")
            self.service = None

    def is_connected(self) -> bool:
        return self.service is not None

    # ============================================================
    # Engagement Tracker
    # ============================================================
    def add_engagement(self, data: dict):
        """Add a row to the Engagement Tracker sheet."""
        if not self.service or not TRACKER_SHEET_ID:
            return False

        row = [
            data.get("date", datetime.now().strftime("%Y-%m-%d")),
            data.get("client", ""),
            data.get("engagement_type", ""),
            data.get("industry", "Creative Economy"),
            data.get("constraint", ""),
            data.get("framework", ""),
            data.get("outcome", ""),
            data.get("content_potential", ""),
            data.get("followup", ""),
            data.get("notes", ""),
        ]

        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=TRACKER_SHEET_ID,
                range="Engagement Tracker!A:J",
                valueInputOption="USER_ENTERED",
                body={"values": [row]}
            ).execute()
            return True
        except Exception as e:
            print(f"Error adding engagement: {e}")
            return False

    def add_content_idea(self, data: dict):
        """Add to the Content Pipeline sheet."""
        if not self.service or not TRACKER_SHEET_ID:
            return False

        row = [
            data.get("source", ""),
            data.get("idea", ""),
            data.get("format", ""),
            data.get("channel", ""),
            data.get("priority", "Medium"),
            "Backlog",
        ]

        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=TRACKER_SHEET_ID,
                range="Content Pipeline!A:F",
                valueInputOption="USER_ENTERED",
                body={"values": [row]}
            ).execute()
            return True
        except Exception as e:
            print(f"Error adding content idea: {e}")
            return False

    # ============================================================
    # Brand Calendar
    # ============================================================
    def update_calendar_status(self, day: int, status: str):
        """Update status column for a specific day in the calendar."""
        if not self.service or not CALENDAR_SHEET_ID:
            return False

        row = day + 1  # Row 1 is header, Day 1 = Row 2
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=CALENDAR_SHEET_ID,
                range=f"30-Day Calendar!I{row}",
                valueInputOption="USER_ENTERED",
                body={"values": [[status]]}
            ).execute()
            return True
        except Exception as e:
            print(f"Error updating calendar: {e}")
            return False

    def get_today_content(self):
        """Get today's planned content from the calendar."""
        if not self.service or not CALENDAR_SHEET_ID:
            return None

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=CALENDAR_SHEET_ID,
                range="30-Day Calendar!A2:J31"
            ).execute()
            rows = result.get("values", [])

            today = datetime.now().strftime("%b %d")
            for row in rows:
                if len(row) > 1 and row[1] == today:
                    return {
                        "day": row[0] if len(row) > 0 else "",
                        "date": row[1] if len(row) > 1 else "",
                        "day_of_week": row[2] if len(row) > 2 else "",
                        "channel": row[3] if len(row) > 3 else "",
                        "content_type": row[4] if len(row) > 4 else "",
                        "title": row[5] if len(row) > 5 else "",
                        "hook": row[6] if len(row) > 6 else "",
                        "cta": row[7] if len(row) > 7 else "",
                        "status": row[8] if len(row) > 8 else "",
                        "notes": row[9] if len(row) > 9 else "",
                    }
            return None
        except Exception as e:
            print(f"Error reading calendar: {e}")
            return None

    def get_full_calendar(self):
        """Get the entire content calendar for the dashboard."""
        if not self.service or not CALENDAR_SHEET_ID:
            return []

        try:
            # First, get the header row to understand column layout
            header_result = self.service.spreadsheets().values().get(
                spreadsheetId=CALENDAR_SHEET_ID,
                range="30-Day Calendar!A1:Z1"
            ).execute()
            headers = header_result.get("values", [[]])[0]
            headers = [h.strip().lower() for h in headers]

            # Then get all data rows
            result = self.service.spreadsheets().values().get(
                spreadsheetId=CALENDAR_SHEET_ID,
                range="30-Day Calendar!A2:Z100"
            ).execute()
            rows = result.get("values", [])

            calendar_items = []
            for row in rows:
                if not row or not any(cell.strip() for cell in row if cell):
                    continue
                item = {}
                for i, header in enumerate(headers):
                    item[header] = row[i].strip() if i < len(row) and row[i] else ""
                calendar_items.append(item)
            return calendar_items
        except Exception as e:
            print(f"Error reading full calendar: {e}")
            return []

    def get_upcoming_content(self, platform: str = None):
        """Get upcoming/scheduled content, optionally filtered by platform."""
        items = self.get_full_calendar()
        if not items:
            return []

        today = datetime.now()
        upcoming = []
        for item in items:
            # Normalize status
            status = (item.get("status", "") or "").lower().strip()
            # Include items that are scheduled, planned, draft, or not yet done
            if status in ("published", "posted", "done", "complete"):
                continue

            # Filter by platform if specified
            if platform:
                channel = (item.get("channel", "") or item.get("platform", "")).lower()
                if platform.lower() not in channel:
                    continue

            upcoming.append(item)
        return upcoming

    # ============================================================
    # Metrics
    # ============================================================
    def update_metric(self, sheet_name: str, cell: str, value):
        """Update a specific cell in any sheet."""
        if not self.service:
            return False

        sheet_id = TRACKER_SHEET_ID or CALENDAR_SHEET_ID
        if not sheet_id:
            return False

        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!{cell}",
                valueInputOption="USER_ENTERED",
                body={"values": [[value]]}
            ).execute()
            return True
        except Exception as e:
            print(f"Error updating metric: {e}")
            return False
