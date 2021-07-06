import shutil
import time

import psutil
from telegram import InlineKeyboardMarkup
from telegram.message import Message
from telegram.update import Update

from bot import (
    AUTO_DELETE_MESSAGE_DURATION,
    LOGGER,
    bot,
    botStartTime,
    download_dict,
    download_dict_lock,
    status_reply_dict,
    status_reply_dict_lock,
)
from bot.helper.ext_utils.bot_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_message,
    get_readable_time,
)


def send_message(text: str, bot, update: Update):
    try:
        return bot.send_message(
            update.message.chat_id,
            reply_to_message_id=update.message.message_id,
            text=text,
            parse_mode="HTMl",
        )
    except Exception as e:
        LOGGER.error(str(e))


def send_markup(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    return bot.send_message(
        update.message.chat_id,
        reply_to_message_id=update.message.message_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTMl",
    )


def edit_message(text: str, message: Message, reply_markup=None):
    try:
        bot.edit_message_text(
            text=text,
            message_id=message.message_id,
            chat_id=message.chat.id,
            reply_markup=reply_markup,
            parse_mode="HTMl",
        )
    except Exception as e:
        LOGGER.error(str(e))


def delete_message(bot, message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))


def send_log_file(bot, update: Update):
    with open("log.txt", "rb") as f:
        bot.send_document(
            document=f,
            filename=f.name,
            reply_to_message_id=update.message.message_id,
            chat_id=update.message.chat_id,
        )


def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            delete_message(bot, cmd_message)
            delete_message(bot, bot_message)
        except AttributeError:
            pass


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                delete_message(bot, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


def update_all_messages():
    total, used, free = shutil.disk_usage(".")
    free = get_readable_file_size(free)
    currentTime = get_readable_time(time.time() - botStartTime)
    msg = get_readable_message()
    msg += (
        f"<b>CPU:</b> {psutil.cpu_percent()}%"
        f" <b>RAM:</b> {psutil.virtual_memory().percent}%"
        f" <b>DISK:</b> {psutil.disk_usage('/').percent}%"
    )
    with download_dict_lock:
        dlspeed_bytes = 0
        uldl_bytes = 0
        for download in list(download_dict.values()):
            speedy = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if "K" in speedy:
                    dlspeed_bytes += float(speedy.split("K")[0]) * 1024
                elif "M" in speedy:
                    dlspeed_bytes += float(speedy.split("M")[0]) * 1048576
            if download.status() == MirrorStatus.STATUS_UPLOADING:
                if "KB/s" in speedy:
                    uldl_bytes += float(speedy.split("K")[0]) * 1024
                elif "MB/s" in speedy:
                    uldl_bytes += float(speedy.split("M")[0]) * 1048576
        dlspeed = get_readable_file_size(dlspeed_bytes)
        ulspeed = get_readable_file_size(uldl_bytes)
        msg += f"\n<b>FREE:</b> {free} | <b>UPTIME:</b> {currentTime}\n<b>DL:</b> {dlspeed}ps 🔻 | <b>UL:</b> {ulspeed}ps 🔺\n"
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                if len(msg) == 0:
                    msg = "Starting DL"
                try:
                    edit_message(msg, status_reply_dict[chat_id])
                except Exception as e:
                    LOGGER.error(str(e))
                status_reply_dict[chat_id].text = msg


def send_status_message(msg, bot):
    total, used, free = shutil.disk_usage(".")
    free = get_readable_file_size(free)
    currentTime = get_readable_time(time.time() - botStartTime)
    progress = get_readable_message()
    progress += (
        f"<b>CPU:</b> {psutil.cpu_percent()}%"
        f" <b>RAM:</b> {psutil.virtual_memory().percent}%"
        f" <b>DISK:</b> {psutil.disk_usage('/').percent}%"
    )
    with download_dict_lock:
        dlspeed_bytes = 0
        uldl_bytes = 0
        for download in list(download_dict.values()):
            speedy = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if "K" in speedy:
                    dlspeed_bytes += float(speedy.split("K")[0]) * 1024
                elif "M" in speedy:
                    dlspeed_bytes += float(speedy.split("M")[0]) * 1048576
            if download.status() == MirrorStatus.STATUS_UPLOADING:
                if "KB/s" in speedy:
                    uldl_bytes += float(speedy.split("K")[0]) * 1024
                elif "MB/s" in speedy:
                    uldl_bytes += float(speedy.split("M")[0]) * 1048576
        dlspeed = get_readable_file_size(dlspeed_bytes)
        ulspeed = get_readable_file_size(uldl_bytes)
        progress += f"\n<b>FREE:</b> {free} | <b>UPTIME:</b> {currentTime}\n<b>DL:</b> {dlspeed}ps 🔻 | <b>UL:</b> {ulspeed}ps 🔺\n"
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.message.chat.id]
                delete_message(bot, message)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
                pass
        if len(progress) == 0:
            progress = "Starting DL"
        message = send_message(progress, bot, msg)
        status_reply_dict[msg.message.chat.id] = message


# Implement by https://github.com/jusidama18
# Setting Message
def get_text(message: Message):  # -> None | str: #TODO python 3.10
    """Extract Text From Commands"""
    text_to_return = message.text
    if message.text is None:
        return None
    if " " in text_to_return:
        try:
            return message.text.split(None, 1)[1]
        except IndexError:
            return None
    else:
        return None
