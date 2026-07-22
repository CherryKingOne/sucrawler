from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class BrowserEvent:
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserStartedEvent(BrowserEvent):
    event_type: str = "browser_started"
    debug_port: int = 0
    browser_name: str = ""


@dataclass
class BrowserStoppedEvent(BrowserEvent):
    event_type: str = "browser_stopped"


@dataclass
class PageCreatedEvent(BrowserEvent):
    event_type: str = "page_created"
    page_id: str = ""
    url: str = ""


@dataclass
class PageClosedEvent(BrowserEvent):
    event_type: str = "page_closed"
    page_id: str = ""


@dataclass
class PageNavigatedEvent(BrowserEvent):
    event_type: str = "page_navigated"
    page_id: str = ""
    url: str = ""
    status_code: int = 0


@dataclass
class NetworkRequestEvent(BrowserEvent):
    event_type: str = "network_request"
    request_id: str = ""
    url: str = ""
    method: str = ""
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class NetworkResponseEvent(BrowserEvent):
    event_type: str = "network_response"
    request_id: str = ""
    url: str = ""
    status_code: int = 0
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class LoginStateChangedEvent(BrowserEvent):
    event_type: str = "login_state_changed"
    is_logged_in: bool = False
    platform: str = ""
