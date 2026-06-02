"""
Google Calendar integration for ARIA.
Fetches upcoming events and formats them as context ARIA can reference naturally.

First-time setup:
  1. Download OAuth credentials from Google Cloud Console → save as credentials.json
  2. Run: python -c "from agent_core.calendar_fetcher import authenticate; authenticate()"
  3. Browser opens → approve → token.json saved → done
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional

CREDS_FILE = Path(__file__).parent.parent / "credentials.json"
TOKEN_FILE  = Path(__file__).parent.parent / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


def authenticate() -> Optional[object]:
    """Run OAuth flow once to get and save token. Returns service or None."""
    if not GOOGLE_AVAILABLE:
        print("  [Calendar] google packages not installed")
        return None
    if not CREDS_FILE.exists():
        print(f"  [Calendar] credentials.json not found at {CREDS_FILE}")
        return None

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"  [Calendar] Token saved to {TOKEN_FILE}")

    return build("calendar", "v3", credentials=creds)


def _get_service() -> Optional[object]:
    """Return authenticated service, or None if not set up."""
    if not GOOGLE_AVAILABLE or not TOKEN_FILE.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"  [Calendar] auth error: {e}")
        return None


def get_upcoming_events(days: int = 7) -> List[Dict]:
    """Return upcoming events for the next *days* days."""
    service = _get_service()
    if not service:
        return []

    now   = datetime.now(timezone.utc)
    until = now + timedelta(days=days)

    try:
        result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=until.isoformat(),
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for item in result.get("items", []):
            start = item["start"].get("dateTime", item["start"].get("date", ""))
            end   = item["end"].get("dateTime",   item["end"].get("date",   ""))

            # Parse datetime
            try:
                if "T" in start:
                    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    label = dt.astimezone().strftime("%A %b %d at %I:%M %p")
                    all_day = False
                else:
                    dt = datetime.strptime(start, "%Y-%m-%d")
                    label = dt.strftime("%A %b %d (all day)")
                    all_day = True
            except Exception:
                label = start
                dt    = now
                all_day = True

            events.append({
                "title":   item.get("summary", "Untitled"),
                "start":   label,
                "dt":      dt,
                "all_day": all_day,
                "location": item.get("location", ""),
                "description": (item.get("description", "") or "")[:120],
            })

        return events
    except Exception as e:
        print(f"  [Calendar] fetch error: {e}")
        return []


def format_for_context(events: List[Dict]) -> str:
    """Format events as a compact context block for ARIA."""
    if not events:
        return ""

    now   = datetime.now(timezone.utc)
    today = now.date()

    lines = ["[Upcoming schedule]"]
    for ev in events:
        dt   = ev["dt"]
        date = dt.date() if hasattr(dt, "date") else today

        if date == today:
            prefix = "Today"
        elif date == today + timedelta(days=1):
            prefix = "Tomorrow"
        else:
            days_away = (date - today).days
            prefix = f"In {days_away} days"

        line = f"  • {prefix} — {ev['title']} ({ev['start']})"
        if ev["location"]:
            line += f" @ {ev['location']}"
        lines.append(line)

    lines.append("[End schedule]")
    return "\n".join(lines)


def is_configured() -> bool:
    return GOOGLE_AVAILABLE and TOKEN_FILE.exists()
