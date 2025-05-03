import datetime
import functools
import json
import logging
import os
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
_LOGGER = logging.getLogger(__name__)

CHILDREN: list = ",".split(os.getenv("CHILDREN"))


class AulaClient:
    """Aula client for connecting and fetching specific data."""

    def __init__(self, username: str, password: str):
        """Initialize the Aula client with username and password."""
        self._username = username
        self._password = password
        self._session = None
        self.apiurl = "https://www.aula.dk/api/v20"
        self._profiles = None
        self.active_child = None

    def _login(self) -> bool:
        """Authenticate with Aula and establish a session."""
        _LOGGER.debug("Attempting to log in to Aula")
        self._session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/112.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
        params = {"type": "unilogin"}
        response = self._session.get(
            "https://login.aula.dk/auth/login.php",
            params=params,
            headers=headers,
            verify=True,
        )

        html = BeautifulSoup(response.text, "lxml")
        url = html.form["action"]
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = {"selectedIdp": "uni_idp"}
        response = self._session.post(url, headers=headers, data=data, verify=True)

        user_data = {
            "username": self._username,
            "password": self._password,
            "selected-aktoer": "KONTAKT",
        }
        redirects = 0
        success = False
        while not success and redirects < 10:
            html = BeautifulSoup(response.text, "lxml")
            url = html.form["action"]
            post_data = {
                input["name"]: input["value"]
                for input in html.find_all("input")
                if input.has_attr("name") and input.has_attr("value")
            }
            post_data.update(
                {
                    key: user_data[key]
                    for key in user_data
                    if key in post_data or key not in post_data
                }
            )
            response = self._session.post(url, data=post_data, verify=True)
            if response.url == "https://www.aula.dk:443/portal/":
                success = True
            redirects += 1

        if not success:
            _LOGGER.error("Failed to log in after multiple redirects")
            raise Exception("Login failed")

        apiver = 20
        api_success = False
        while not api_success:
            self.apiurl = f"https://www.aula.dk/api/v{apiver}"
            _LOGGER.debug(f"Trying API at {self.apiurl}")
            response = self._session.get(
                self.apiurl + "?method=profiles.getProfilesByLogin", verify=True
            )
            if response.status_code == 410:
                apiver += 1
            elif response.status_code == 403:
                _LOGGER.error("Access denied. Check credentials.")
                raise Exception("Invalid credentials or access denied")
            elif response.status_code == 200:
                self._profiles = response.json()["data"]["profiles"]
                api_success = True
            else:
                _LOGGER.error(f"Unexpected status code: {response.status_code}")
                raise Exception("API connection failed")

        _LOGGER.debug("Login successful. API found at " + self.apiurl)
        self.ids = {
            c.get("name").split(" ")[0]: c.get("id")
            for c in self._profiles[0].get("children")
        }
        return True

    def _ensure_session(self):
        """Ensure the session is active, re-authenticate if necessary."""
        if not self._session:
            self._login()
        response = self._session.get(
            self.apiurl + "?method=profiles.getProfilesByLogin", verify=True
        ).json()
        if response["status"]["message"] != "OK":
            _LOGGER.debug("Session expired, re-authenticating")
            self._login()

    def require_active_child(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.active_child:
                raise ValueError(
                    "Remember to set active child with client.set_active_child(name:str)"
                )
            return func(self, *args, **kwargs)

        return wrapper

    def set_active_child(self, name: str) -> None:
        """Set the active child by name."""
        self.active_child = name

    @require_active_child
    def get_child_id(self) -> int:
        """Get the child ID for the active child."""
        self._ensure_session()
        return self.ids.get(self.active_child)

    @require_active_child
    def get_institution(self) -> str:
        """Get the institution name for the active child."""
        self._ensure_session()
        return [
            c["institutionProfile"]["institutionName"]
            for c in self._profiles[0].get("children")
            if self.active_child in c["name"]
        ][0]

    def fetch_basic_data(self) -> str:
        """Fetch basic profile data from Aula."""
        self._ensure_session()
        children_data = {}
        for profile in self._profiles:
            for child in profile["children"]:
                child_id = str(child["id"])
                children_data[child_id] = {
                    "name": child["name"],
                    "institution": child["institutionProfile"]["institutionName"],
                }
        _LOGGER.debug(f"Fetched basic data: {children_data}")
        return str(children_data)

    @require_active_child
    def fetch_daily_overview(self) -> dict:
        """Fetch daily overview (presence data) for the active child."""
        self._ensure_session()
        overview = {}
        response = self._session.get(
            self.apiurl
            + f"?method=presence.getDailyOverview&childIds[]={self.get_child_id()}",
            verify=True,
        ).json()
        if response["data"]:
            overview[self.get_child_id()] = response["data"][0]
        else:
            _LOGGER.debug(f"No presence data for child {self.get_child_id()}")
            overview[self.get_child_id()] = None

        _LOGGER.debug(f"Daily overview: {overview}")
        return overview

    def fetch_messages(self) -> list:
        """Fetch the latest unread messages."""
        self._ensure_session()
        response = self._session.get(
            self.apiurl
            + "?method=messaging.getThreads&sortOn=date&orderDirection=desc&page=0",
            verify=True,
        ).json()

        messages = []
        for thread in response["data"]["threads"]:
            if not thread["read"]:
                thread_response = self._session.get(
                    self.apiurl
                    + f"?method=messaging.getMessagesForThread&threadId={thread['id']}&page=0",
                    verify=True,
                ).json()

                if thread_response["status"]["code"] == 403:
                    messages.append(
                        {
                            "subject": "Følsom besked",
                            "text": "Log ind på Aula med MitID for at læse denne besked.",
                            "sender": "Ukendt afsender",
                        }
                    )
                else:
                    for msg in thread_response["data"]["messages"]:
                        if msg["messageType"] == "Message":
                            messages.append(
                                {
                                    "subject": thread_response["data"].get(
                                        "subject", ""
                                    ),
                                    "text": msg.get("text", {}).get(
                                        "html", msg.get("text", "intet indhold...")
                                    ),
                                    "sender": msg["sender"].get(
                                        "fullName", "Ukendt afsender"
                                    ),
                                }
                            )

        _LOGGER.debug(f"Latest messages: {messages}")
        return messages

    def fetch_calendar(self, days: int = 14, structured: bool = True) -> list:
        """Fetch calendar events for the next specified number of days.

        Args:
            days: Number of days to fetch calendar events for
            structured: If True, returns events organized by day instead of a flat list
        """
        self._ensure_session()
        csrf_token = self._session.cookies.get_dict()["Csrfp-Token"]
        headers = {"csrfp-token": csrf_token, "content-type": "application/json"}

        start = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d 00:00:00.0000%z"
        )
        end = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
        ).strftime("%Y-%m-%d 00:00:00.0000%z")
        post_data = json.dumps(
            {
                "instProfileIds": list(self.ids.values()),
                "resourceIds": [],
                "start": start,
                "end": end,
            }
        )

        response = self._session.post(
            self.apiurl + "?method=calendar.getEventsByProfileIdsAndResourceIds",
            data=post_data,
            headers=headers,
            verify=True,
        ).json()

        if response["status"]["message"] != "OK":
            _LOGGER.warning(f"Failed to fetch calendar: {response}")
            return []

        events = [
            res
            for res in response["data"]
            if self.get_child_id() in res["belongsToProfiles"]
        ]
        _LOGGER.debug(f"Calendar events: {events}")

        if structured:
            return self._structure_calendar_by_day(events)
        return events

    def _structure_calendar_by_day(self, events: list) -> dict:
        """Organize calendar events by day.

        Args:
            events: List of calendar events

        Returns:
            Dictionary with dates as keys and lists of events as values
        """
        daily_events = defaultdict(list)

        for event in events:
            # Extract date from the startDateTime (format: "2025-03-17T07:00:00+00:00")
            start_datetime = datetime.datetime.fromisoformat(
                event["startDateTime"].replace("Z", "+00:00")
            )
            date_str = start_datetime.strftime("%Y-%m-%d")

            # Add formatted time to the event for display purposes
            event[
                "formatted_time"
            ] = f"{start_datetime.strftime('%H:%M')} - {datetime.datetime.fromisoformat(event['endDateTime'].replace('Z', '+00:00')).strftime('%H:%M')}"

            # Add event to the corresponding day
            daily_events[date_str].append(event)

        # Sort events within each day by start time
        for date in daily_events:
            daily_events[date].sort(key=lambda x: x["startDateTime"])

        return dict(daily_events)

    def fetch_gallery(self) -> list:
        """Fetch gallery items (images and posts) from Aula."""
        self._ensure_session()
        child_ids = [
            str(child["id"])
            for profile in self._profiles
            for child in profile["children"]
        ]
        inst_profile_ids = ",".join(child_ids)

        response = self._session.get(
            self.apiurl
            + f"?method=gallery.getAlbums&institutionProfileIds={inst_profile_ids}&page=0",
            verify=True,
        ).json()

        if response["status"]["message"] != "OK":
            _LOGGER.warning(f"Failed to fetch gallery: {response}")
            return []

        gallery_items = []
        for album in response["data"]["albums"]:
            album_response = self._session.get(
                self.apiurl + f"?method=gallery.getAlbum&id={album['id']}",
                verify=True,
            ).json()
            if album_response["status"]["message"] == "OK":
                for item in album_response["data"]["pictures"]:
                    gallery_items.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "created": item.get("created", ""),
                        }
                    )

        _LOGGER.debug(f"Gallery items: {gallery_items}")
        return gallery_items

    def custom_api_call(self, uri: str, post_data: str = None) -> dict:
        """Make a custom API call to Aula."""
        self._ensure_session()
        csrf_token = self._session.cookies.get_dict()["Csrfp-Token"]
        headers = {"csrfp-token": csrf_token, "content-type": "application/json"}

        if post_data:
            try:
                json.loads(post_data)
                response = self._session.post(
                    self.apiurl + uri,
                    headers=headers,
                    json=json.loads(post_data),
                    verify=True,
                )
            except json.JSONDecodeError:
                _LOGGER.error("Invalid JSON in post_data")
                return {"result": "Fail - invalid JSON"}
        else:
            response = self._session.get(
                self.apiurl + uri, headers=headers, verify=True
            )

        try:
            return response.json()
        except Exception:
            return {"raw_response": response.text}


client = AulaClient(os.getenv("USERNAME"), os.getenv("PASSWORD"))

# Fetch basic profile data
# basic_data = client.fetch_basic_data()
# print("Basic Data:", basic_data)

# Fetch daily overview
# overview = client.fetch_daily_overview("Olli")
# print("Daily Overview:", overview)

# Fetch latest messages
# messages = client.fetch_messages()
# print("Messages:", messages)

# Fetch calendar for next 7 days
"""client.set_active_child("Nellie")
calendar = client.fetch_calendar(days=7, structured=True)
print("Calendar Events by Day:")
for date, events in calendar.items():
    print(f"\n=== {date} ===")
    for event in events:
        teacher = (
            event.get("lesson", {})
            .get("participants", [{}])[0]
            .get("teacherName", "Unknown")
        )
        print(f"{event['formatted_time']} - {event['title']} (Teacher: {teacher})")
    break"""

# # Fetch gallery items
# gallery = client.fetch_gallery()
# print("Gallery Items:", gallery)
