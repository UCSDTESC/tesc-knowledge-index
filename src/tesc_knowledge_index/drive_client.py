from __future__ import annotations

from googleapiclient.discovery import build

from .auth import get_credentials


def build_drive_service(account: str):
    creds = get_credentials(account)
    return build("drive", "v3", credentials=creds)
