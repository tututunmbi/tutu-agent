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
        self._client_email = None
        self._init_service()

    def _init_service(self):
        """Initialize Google Sheets API service."""
        if not GOOGLE_CREDENTIALS:
            return

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_dict = json.loads(GOOGLE_CREDENTIALS)
            self._client_email = creds_dict.get("client_email", "")
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            self.service = build("sheets", "v4", credentials=creds)
        except Exception as e:
            print(f"Google Sheets not configured: {e}")
            self.service = None

    def is_connected(self) -> bool:
        return self.service is not None

    def get_service_account_email(self) -> str:
        """Return the service account email for sharing sheets."""
        return self._client_email or ""

    # ============================================================
    # Generic helpers
    # ============================================================
    def _read_sheet(self, spreadsheet_id: str, range_str: str):
        """Read values from a sheet range."""
        if not self.service:
            return None
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_str
            ).execute()
            return result.get("values", [])
        except Exception as e:
            print(f"Error reading {range_str}: {e}")
            return None

    def _append_row(self, spreadsheet_id: str, range_str: str, row: list):
        """Append a row to a sheet."""
        if not self.service:
            return False
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_str,
                valueInputOption="USER_ENTERED",
                body={"values": [row]}
            ).execute()
            return True
        except Exception as e:
            print(f"Error appending to {range_str}: {e}")
            return False

    def _update_range(self, spreadsheet_id: str, range_str: str, values: list):
        """Update a specific range with values."""
        if not self.service:
            return False
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_str,
                valueInputOption="USER_ENTERED",
                body={"values": values}
            ).execute()
            return True
        except Exception as e:
            print(f"Error updating {range_str}: {e}")
            return False

    # ============================================================
    # Engagement Tracker — CRUD
    # ============================================================
    def add_engagement(self, data: dict):
        """Add a row to the Engagement Tracker sheet."""
        if not TRACKER_SHEET_ID:
            return {"success": False, "error": "TRACKER_SHEET_ID not configured"}

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

        ok = self._append_row(TRACKER_SHEET_ID, "Engagement Tracker!A:J", row)
        return {"success": ok, "row": row}

    def get_engagements(self, limit: int = 20):
        """Read recent engagements from the tracker."""
        if not TRACKER_SHEET_ID:
            return {"success": False, "error": "TRACKER_SHEET_ID not configured"}

        rows = self._read_sheet(TRACKER_SHEET_ID, "Engagement Tracker!A1:J200")
        if rows is None:
            return {"success": False, "error": "Could not read engagement tracker"}

        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        # Return most recent first
        entries = []
        for row in reversed(data_rows[-limit:]):
            entry = {}
            for i, h in enumerate(headers):
                entry[h] = row[i] if i < len(row) else ""
            entries.append(entry)
        return {"success": True, "count": len(entries), "entries": entries}

    def search_engagements(self, query: str):
        """Search engagements by client name, constraint, or notes."""
        result = self.get_engagements(limit=200)
        if not result.get("success"):
            return result

        query_lower = query.lower()
        matches = []
        for entry in result["entries"]:
            searchable = " ".join(str(v) for v in entry.values()).lower()
            if query_lower in searchable:
                matches.append(entry)
        return {"success": True, "count": len(matches), "matches": matches}

    # ============================================================
    # Content Pipeline — CRUD
    # ============================================================
    def add_content_idea(self, data: dict):
        """Add to the Content Pipeline sheet."""
        if not TRACKER_SHEET_ID:
            return {"success": False, "error": "TRACKER_SHEET_ID not configured"}

        row = [
            data.get("source", ""),
            data.get("idea", ""),
            data.get("format", ""),
            data.get("channel", ""),
            data.get("priority", "Medium"),
            data.get("status", "Backlog"),
        ]

        ok = self._append_row(TRACKER_SHEET_ID, "Content Pipeline!A:F", row)
        return {"success": ok, "row": row}

    def get_content_ideas(self, status_filter: str = None):
        """Read content ideas from the pipeline."""
        if not TRACKER_SHEET_ID:
            return {"success": False, "error": "TRACKER_SHEET_ID not configured"}

        rows = self._read_sheet(TRACKER_SHEET_ID, "Content Pipeline!A1:F200")
        if rows is None:
            return {"success": False, "error": "Could not read content pipeline"}

        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        entries = []
        for i, row in enumerate(data_rows):
            entry = {"row_number": i + 2}  # 1-indexed, skip header
            for j, h in enumerate(headers):
                entry[h] = row[j] if j < len(row) else ""
            if status_filter:
                if entry.get("Status", "").lower() != status_filter.lower():
                    continue
            entries.append(entry)
        return {"success": True, "count": len(entries), "ideas": entries}

    # ============================================================
    # Brand Calendar — Full CRUD
    # ============================================================
    def get_full_calendar(self):
        """Get the entire content calendar for the dashboard."""
        if not self.service or not CALENDAR_SHEET_ID:
            return []

        try:
            header_result = self.service.spreadsheets().values().get(
                spreadsheetId=CALENDAR_SHEET_ID,
                range="30-Day Calendar!A1:Z1"
            ).execute()
            headers = header_result.get("values", [[]])[0]
            headers = [h.strip().lower() for h in headers]

            result = self.service.spreadsheets().values().get(
                spreadsheetId=CALENDAR_SHEET_ID,
                range="30-Day Calendar!A2:Z100"
            ).execute()
            rows = result.get("values", [])

            calendar_items = []
            for row_idx, row in enumerate(rows):
                if not row or not any(cell.strip() for cell in row if cell):
                    continue
                item = {"_row": row_idx + 2}  # Track actual row number
                for i, header in enumerate(headers):
                    item[header] = row[i].strip() if i < len(row) and row[i] else ""
                calendar_items.append(item)
            return calendar_items
        except Exception as e:
            print(f"Error reading full calendar: {e}")
            return []

    def get_calendar_headers(self):
        """Get the column headers from the calendar sheet."""
        if not self.service or not CALENDAR_SHEET_ID:
            return []
        rows = self._read_sheet(CALENDAR_SHEET_ID, "30-Day Calendar!A1:Z1")
        if rows and rows[0]:
            return rows[0]
        return []

    def get_upcoming_content(self, platform: str = None):
        """Get upcoming/scheduled content, optionally filtered by platform."""
        items = self.get_full_calendar()
        if not items:
            return []

        upcoming = []
        for item in items:
            status = (item.get("status", "") or "").lower().strip()
            if status in ("published", "posted", "done", "complete"):
                continue
            if platform:
                channel = (item.get("channel", "") or item.get("primary channel", "") or item.get("platform", "")).lower()
                if platform.lower() not in channel:
                    continue
            upcoming.append(item)
        return upcoming

    def update_calendar_status(self, day: int, status: str):
        """Update status column for a specific day in the calendar."""
        if not self.service or not CALENDAR_SHEET_ID:
            return {"success": False, "error": "Calendar not configured"}

        # Find the status column dynamically
        headers = self.get_calendar_headers()
        status_col_idx = None
        for i, h in enumerate(headers):
            if h.lower().strip() == "status":
                status_col_idx = i
                break
        if status_col_idx is None:
            status_col_idx = 8  # Default to column I

        col_letter = chr(65 + status_col_idx)  # A=0, B=1, ...
        row = day + 1  # Row 1 is header, Day 1 = Row 2

        ok = self._update_range(
            CALENDAR_SHEET_ID,
            f"30-Day Calendar!{col_letter}{row}",
            [[status]]
        )
        return {"success": ok, "day": day, "new_status": status}

    def update_calendar_entry(self, day: int, updates: dict):
        """Update any fields for a specific day in the calendar.

        updates can contain any column header as key, e.g.:
        {"title / topic": "New title", "status": "In Progress", "notes": "Updated"}
        """
        if not self.service or not CALENDAR_SHEET_ID:
            return {"success": False, "error": "Calendar not configured"}

        headers = self.get_calendar_headers()
        if not headers:
            return {"success": False, "error": "Could not read calendar headers"}

        header_lower = [h.lower().strip() for h in headers]
        row_num = day + 1  # Row 1 is header

        # Read the current row
        current = self._read_sheet(
            CALENDAR_SHEET_ID,
            f"30-Day Calendar!A{row_num}:{chr(64 + len(headers))}{row_num}"
        )
        if not current or not current[0]:
            return {"success": False, "error": f"No data found for day {day}"}

        row_data = current[0]
        # Extend row_data to match headers length
        while len(row_data) < len(headers):
            row_data.append("")

        # Apply updates
        updated_fields = []
        for key, value in updates.items():
            key_lower = key.lower().strip()
            for i, h in enumerate(header_lower):
                if key_lower == h or key_lower in h or h in key_lower:
                    row_data[i] = str(value)
                    updated_fields.append(headers[i])
                    break

        if not updated_fields:
            return {"success": False, "error": f"No matching columns found for: {list(updates.keys())}. Available: {headers}"}

        # Write back the full row
        ok = self._update_range(
            CALENDAR_SHEET_ID,
            f"30-Day Calendar!A{row_num}:{chr(64 + len(headers))}{row_num}",
            [row_data]
        )
        return {"success": ok, "day": day, "updated_fields": updated_fields}

    def add_calendar_entry(self, data: dict):
        """Add a new entry to the brand calendar.

        data should contain keys matching column headers, e.g.:
        {"day": "31", "date": "Apr 15", "day of week": "Tuesday",
         "primary channel": "Instagram", "content type": "Reel",
         "title / topic": "...", "hook / angle": "...", "cta": "...",
         "status": "Planned", "notes": ""}
        """
        if not self.service or not CALENDAR_SHEET_ID:
            return {"success": False, "error": "Calendar not configured"}

        headers = self.get_calendar_headers()
        if not headers:
            return {"success": False, "error": "Could not read calendar headers"}

        header_lower = [h.lower().strip() for h in headers]
        row = []
        for h in header_lower:
            matched = False
            for key, value in data.items():
                if key.lower().strip() == h or key.lower().strip() in h or h in key.lower().strip():
                    row.append(str(value))
                    matched = True
                    break
            if not matched:
                row.append("")

        ok = self._append_row(CALENDAR_SHEET_ID, "30-Day Calendar!A:Z", row)
        return {"success": ok, "entry": dict(zip(headers, row))}

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
            # Also try other date formats
            today_alt = datetime.now().strftime("%-d %b")  # "24 Mar"
            today_alt2 = datetime.now().strftime("%b %-d")  # "Mar 24"

            for row in rows:
                if len(row) > 1:
                    date_val = row[1].strip()
                    if date_val in (today, today_alt, today_alt2):
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

    # ============================================================
    # Generic sheet read/write for any tab
    # ============================================================
    def read_sheet_tab(self, spreadsheet_id: str, tab_name: str, max_rows: int = 100):
        """Read an entire tab from any spreadsheet, returning headers + rows as dicts."""
        rows = self._read_sheet(spreadsheet_id, f"{tab_name}!A1:Z{max_rows}")
        if not rows:
            return {"success": False, "error": f"Could not read tab '{tab_name}'"}

        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []

        entries = []
        for i, row in enumerate(data_rows):
            entry = {"_row": i + 2}
            for j, h in enumerate(headers):
                entry[h] = row[j] if j < len(row) else ""
            entries.append(entry)
        return {"success": True, "headers": headers, "count": len(entries), "entries": entries}

    def write_to_cell(self, spreadsheet_id: str, tab_name: str, cell: str, value):
        """Write a value to a specific cell in any tab."""
        ok = self._update_range(spreadsheet_id, f"{tab_name}!{cell}", [[value]])
        return {"success": ok, "cell": f"{tab_name}!{cell}", "value": value}

    def append_to_tab(self, spreadsheet_id: str, tab_name: str, row_data: list):
        """Append a row to any tab."""
        ok = self._append_row(spreadsheet_id, f"{tab_name}!A:Z", row_data)
        return {"success": ok}

    # ============================================================
    # Multi-tab operations for the calendar spreadsheet
    # ============================================================
    def list_calendar_tabs(self):
        """List all tab names in the calendar spreadsheet."""
        if not self.service or not CALENDAR_SHEET_ID:
            return []
        try:
            meta = self.service.spreadsheets().get(
                spreadsheetId=CALENDAR_SHEET_ID
            ).execute()
            return [s["properties"]["title"] for s in meta.get("sheets", [])]
        except Exception as e:
            print(f"Error listing tabs: {e}")
            return []

    def read_calendar_tab(self, tab_name: str, max_rows: int = 100):
        """Read any tab from the brand calendar spreadsheet."""
        if not CALENDAR_SHEET_ID:
            return {"success": False, "error": "CALENDAR_SHEET_ID not configured"}
        return self.read_sheet_tab(CALENDAR_SHEET_ID, tab_name, max_rows)

    def read_tracker_tab(self, tab_name: str, max_rows: int = 200):
        """Read any tab from the engagement tracker spreadsheet."""
        if not TRACKER_SHEET_ID:
            return {"success": False, "error": "TRACKER_SHEET_ID not configured"}
        return self.read_sheet_tab(TRACKER_SHEET_ID, tab_name, max_rows)

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

        return self._update_range(sheet_id, f"{sheet_name}!{cell}", [[value]])
