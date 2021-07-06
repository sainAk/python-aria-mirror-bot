import logging
import re
import threading
import time

from bot import download_dict, download_dict_lock
from bot.helper.telegram_helper.bot_commands import BotCommands

LOGGER = logging.getLogger(__name__)

MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"

URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"

PROGRESS_MAX_SIZE = 100 // 8
PROGRESS_BAR = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


class MirrorStatus:
    STATUS_UPLOADING = "Uploading...📤"
    STATUS_DOWNLOADING = "Downloading...📥"
    STATUS_WAITING = "Queued...📝"
    STATUS_FAILED = "Failed 🚫. Cleaning Download..."
    STATUS_ARCHIVING = "Archiving...🗜"
    STATUS_EXTRACTING = "Extracting...📂"


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f"{round(size_in_bytes, 2)}{SIZE_UNITS[index]}"
    except IndexError:
        return "File too large"


def get_download_by_gid(gid):
    with download_dict_lock:
        for download in download_dict.values():
            if (
                download.status() != MirrorStatus.STATUS_UPLOADING
                and download.status() != MirrorStatus.STATUS_ARCHIVING
                and download.status() != MirrorStatus.STATUS_EXTRACTING
            ):
                if download.gid() == gid:
                    return download
    return None


def get_all_download():
    with download_dict_lock:
        for download in download_dict.values():
            if (
                download.status() == MirrorStatus.STATUS_DOWNLOADING
                or download.status() == MirrorStatus.STATUS_WAITING
            ):
                return download


def get_progress_bar_string(status) -> str:
    completed = status.processed_bytes() / 8
    total = status.size_raw() / 8
    progress = round(completed * 100 / total) if total else 0
    progress = min(max(progress, 0), 100)
    progress_full = progress // 8
    progress_partial = progress % 8 - 1
    progress_str = PROGRESS_BAR[7] * progress_full
    if progress_partial >= 0:
        progress_str += PROGRESS_BAR[progress_partial]
    progress_str += " " * (PROGRESS_MAX_SIZE - progress_full)
    return f"[{progress_str}]"


def get_readable_message() -> str:
    with download_dict_lock:
        msg = ""
        for download in list(download_dict.values()):
            msg += f"<b>Filename:</b> <code>{download.name()}</code>"
            msg += f'\n<b>By:</b> <a href="tg://user?id={download.message.from_user.id}">{download.message.from_user.first_name}</a>'
            msg += f"\n<b>Status:</b> <i>{download.status()}</i>"
            if (
                download.status() != MirrorStatus.STATUS_ARCHIVING
                and download.status() != MirrorStatus.STATUS_EXTRACTING
                and download.status() != MirrorStatus.STATUS_WAITING
            ):
                msg += f"\n<code>{get_progress_bar_string(download)} {download.progress()}</code>"
                if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                    msg += f"\n<b>Downloaded:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                else:
                    msg += f"\n<b>Uploaded:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                msg += (
                    f"\n<b>Speed:</b> {download.speed()}\n<b>ETA:</b> {download.eta()} "
                )
                # if hasattr(download, 'is_torrent'):
                try:
                    msg += (
                        f"\n<b>Seeders:</b> {download.aria_download().num_seeders}"
                        f" | <b>Peers:</b> {download.aria_download().connections}"
                    )
                except Exception:
                    pass
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                msg += f"\n<b>To Stop:</b> <code>/{BotCommands.CancelMirror} {download.gid()}</code>"
            msg += "\n\n"
        return msg


def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result


def is_url(url: str) -> bool:
    return bool(re.findall(URL_REGEX, url))


def is_gdrive_link(url: str) -> bool:
    return "drive.google.com" in url


def is_mega_link(url: str) -> bool:
    return "mega.nz" in url


def get_mega_link_type(url: str) -> str:
    if "file" in url:
        return "file"
    if "folder" in url or "/#F!" in url:
        return "folder"
    return "file"


def is_magnet(url: str) -> bool:
    return bool(re.findall(MAGNET_REGEX, url))


def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""

    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper
