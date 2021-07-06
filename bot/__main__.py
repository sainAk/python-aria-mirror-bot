# flake8: noqa: F403
import logging
import os
import shutil
import signal
import time
from datetime import datetime
from sys import executable

import psutil
import pytz
from pyrogram import idle
from telegram import BotCommand, ParseMode
from telegram.ext import CommandHandler
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

from bot import (
    IGNORE_PENDING_REQUESTS,
    IMAGE_URL,
    app,
    bot,
    botStartTime,
    dispatcher,
    updater,
)
from bot.helper.ext_utils.fs_utils import clean_all, exit_clean_up, start_cleanup
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_builder import ButtonMaker
from bot.helper.telegram_helper.message_utils import (
    edit_message,
    send_log_file,
    send_message,
)

from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .modules import (
    authorize,
    cancel_mirror,
    clone,
    config,
    count,
    delete,
    eval,
    list_files,
    mediainfo,
    mirror,
    mirror_status,
    shell,
    speedtest,
    torrent_search,
    updates,
    usage,
    watch,
)

LOGGER = logging.getLogger(__name__)


now = datetime.now(pytz.timezone("Asia/Jakarta"))


def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    current = now.strftime("%Y/%m/%d %I:%M:%S %p")
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    stats = (
        f"<b>Bot Uptime:</b> {currentTime}\n"
        f"<b>Start Time:</b> {current}\n"
        f"<b>Total Disk Space:</b> {total}\n"
        f"<b>Used:</b> {used}  "
        f"<b>Free:</b> {free}\n\n"
        f"📊Data Usage📊\n<b>Upload:</b> {sent}\n"
        f"<b>Download:</b> {recv}\n\n"
        f"<b>CPU:</b> {cpuUsage}%\n"
        f"<b>RAM:</b> {memory}%\n"
        f"<b>DISK:</b> {disk}%"
    )
    update.effective_message.reply_photo(IMAGE_URL, stats, parse_mode=ParseMode.HTML)


def start(update, context):
    start_string = f"""
This bot can mirror all your links to Google Drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
"""
    buttons = ButtonMaker()
    buttons.buildbutton("Repo", "https://github.com/sainak/python-aria-mirror-bot/")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    LOGGER.info(
        "UID: {} - UN: {} - MSG: {}".format(
            update.message.chat.id, update.message.chat.username, update.message.text
        )
    )
    uptime = get_readable_time((time.time() - botStartTime))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        if update.message.chat.type == "private":
            send_message(
                f"Hey I'm Alive 🙂\nSince: <code>{uptime}</code>", context.bot, update
            )
        else:
            update.effective_message.reply_photo(
                IMAGE_URL,
                start_string,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
    else:
        send_message(f"Oops! not a Authorized user.", context.bot, update)


def restart(update, context):
    restart_message = send_message("Restarting, Please wait!", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    clean_all()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = send_message("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    edit_message(f"{end_time - start_time} ms", reply)


def log(update, context):
    send_log_file(context.bot, update)


def bot_help(update, context):

    help_string = f"""
/{BotCommands.HelpCommand}: To get this message
/{BotCommands.MirrorCommand} [download_url][magnet_link]: Start mirroring the link to Google Drive
/{BotCommands.TarMirrorCommand} [download_url][magnet_link]: Start mirroring and upload the archived (.tar) version of the download
/{BotCommands.UnzipMirrorCommand} [download_url][magnet_link]: Starts mirroring and if downloaded file is any archive, extracts it to Google Drive
/{BotCommands.CloneCommand} [drive_url]: Copy file/folder to Google Drive
/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive Links
/{BotCommands.WatchCommand} [youtube-dl supported link]: Mirror through youtube-dl. Click /{BotCommands.WatchCommand} for more help
/{BotCommands.TarWatchCommand} [youtube-dl supported link]: Mirror through youtube-dl and tar before uploading
/{BotCommands.CancelMirror}: Reply to the message by which the download was initiated and that download will be cancelled
/{BotCommands.ListCommand} [search term]: Searches the search term in the Google Drive, If found replies with the link
/{BotCommands.StatusCommand}: Shows a status of all the downloads
/{BotCommands.StatsCommand}: Show Stats of the machine the bot is hosted on
/{BotCommands.PingCommand}: Check how long it takes to Ping the Bot
/{BotCommands.SpeedCommand}: Check Internet Speed of the Host
/{BotCommands.MediaInfoCommand}: Get detailed info about replied media (Only for Telegram file)
/{BotCommands.TsHelpCommand}: Get help for Torrent search module
"""

    help_string_adm = f"""
/{BotCommands.DeleteCommand} [drive_url]: Delete file from Google Drive (Only Owner & Sudo)
/{BotCommands.CancelAllCommand}: Cancel all running tasks
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)
/{BotCommands.AuthorizedUsersCommand}: Show authorized users (Only Owner & Sudo)
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner)
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner)
/{BotCommands.RestartCommand}: Restart the bot
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports
/{BotCommands.ConfigMenuCommand}: Get Info Menu about bot config (Owner Only)
/{BotCommands.UpdateCommand}: Update Bot from Upstream Repo (Owner Only)
/{BotCommands.UsageCommand}: To see Heroku Dyno Stats (Owner & Sudo only)
/{BotCommands.MediaInfoCommand}: Get detailed info about replied media (Only for Telegram file)
/{BotCommands.ShellCommand}: Run commands in Shell (Terminal)
"""

    if CustomFilters.sudo_user(update) or CustomFilters.owner_filter(update):
        send_message(help_string + help_string_adm, context.bot, update)
    else:
        send_message(help_string, context.bot, update)


botcmds = [
    BotCommand(f"{BotCommands.HelpCommand}", "Get Detailed Help"),
    BotCommand(f"{BotCommands.MirrorCommand}", "Start Mirroring"),
    BotCommand(f"{BotCommands.TarMirrorCommand}", "Start mirroring and upload as .tar"),
    BotCommand(f"{BotCommands.UnzipMirrorCommand}", "Extract files"),
    BotCommand(f"{BotCommands.CloneCommand}", "Copy file/folder to Drive"),
    BotCommand(f"{BotCommands.CountCommand}", "Count file/folder of Drive link"),
    BotCommand(f"{BotCommands.DeleteCommand}", "Delete file from Drive"),
    BotCommand(f"{BotCommands.WatchCommand}", "Mirror Youtube-dl support link"),
    BotCommand(
        f"{BotCommands.TarWatchCommand}", "Mirror Youtube playlist link as .tar"
    ),
    BotCommand(f"{BotCommands.CancelMirror}", "Cancel a task"),
    BotCommand(f"{BotCommands.CancelAllCommand}", "Cancel all tasks"),
    BotCommand(f"{BotCommands.ListCommand}", "Searches files in Drive"),
    BotCommand(f"{BotCommands.StatusCommand}", "Get Mirror Status message"),
    BotCommand(f"{BotCommands.StatsCommand}", "Bot Usage Stats"),
    BotCommand(f"{BotCommands.PingCommand}", "Ping the Bot"),
    BotCommand(f"{BotCommands.RestartCommand}", "Restart the bot [owner/sudo only]"),
    BotCommand(f"{BotCommands.LogCommand}", "Get the Bot Log [owner/sudo only]"),
    BotCommand(
        f"{BotCommands.MediaInfoCommand}", "Get detailed info about replied media"
    ),
    BotCommand(f"{BotCommands.TsHelpCommand}", "Get help for Torrent search module"),
]


def main():
    start_cleanup()
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    bot.set_my_commands(botcmds)

    start_handler = CommandHandler(
        BotCommands.StartCommand,
        start,
        run_async=True,
    )
    ping_handler = CommandHandler(
        BotCommands.PingCommand,
        ping,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    restart_handler = CommandHandler(
        BotCommands.RestartCommand,
        restart,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
        run_async=True,
    )
    help_handler = CommandHandler(
        BotCommands.HelpCommand,
        bot_help,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    stats_handler = CommandHandler(
        BotCommands.StatsCommand,
        stats,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    log_handler = CommandHandler(
        BotCommands.LogCommand,
        log,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
        run_async=True,
    )
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, exit_clean_up)


app.start()
main()
idle()
