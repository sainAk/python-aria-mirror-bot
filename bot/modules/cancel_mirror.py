from time import sleep

from telegram.ext import CommandHandler

from bot import DOWNLOAD_DIR, dispatcher, download_dict, download_dict_lock
from bot.helper.ext_utils.bot_utils import get_all_download, get_download_by_gid
from bot.helper.ext_utils.fs_utils import clean_download
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import delete_all_messages, send_message


def cancel_mirror(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    mirror_message = None
    if len(args) > 1:
        gid = args[1]
        dl = get_download_by_gid(gid)
        if not dl:
            send_message(f"GID: <code>{gid}</code> Not Found.", context.bot, update)
            return
        mirror_message = dl.message
    elif update.message.reply_to_message:
        mirror_message = update.message.reply_to_message
        with download_dict_lock:
            keys = list(download_dict.keys())
            try:
                dl = download_dict[mirror_message.message_id]
            except Exception:
                pass
    if len(args) == 1:
        msg = f"Please reply to the <code>/{BotCommands.MirrorCommand}</code> message which was used to start the download or send <code>/{BotCommands.CancelMirror} GID</code> to cancel it!"
        if mirror_message and mirror_message.message_id not in keys:
            if (
                BotCommands.MirrorCommand in mirror_message.text
                or BotCommands.TarMirrorCommand in mirror_message.text
                or BotCommands.UnzipMirrorCommand in mirror_message.text
            ):
                msg1 = "Mirror Already Have Been Cancelled"
                send_message(msg1, context.bot, update)
                return
            else:
                send_message(msg, context.bot, update)
                return
        elif not mirror_message:
            send_message(msg, context.bot, update)
            return
    if dl.status() == "Uploading...📤":
        send_message("Upload in Progress, You Can't Cancel It.", context.bot, update)
        return
    elif dl.status() == "Archiving...🔐":
        send_message("Archival in Progress, You Can't Cancel It.", context.bot, update)
        return
    elif dl.status() == "Extracting...📂":
        send_message("Extract in Progress, You Can't Cancel It.", context.bot, update)
        return
    else:
        dl.download().cancel_download()
    sleep(
        3
    )  # incase of any error with ondownloaderror listener, clean_download will delete the folder but the download will stuck in status msg.
    clean_download(f"{DOWNLOAD_DIR}{mirror_message.message_id}/")


def cancel_all(update, context):
    count = 0
    gid = 1
    while True:
        dl = get_all_download()
        if dl:
            if dl.gid() == gid:
                continue
            else:
                gid = dl.gid()
                dl.download().cancel_download()
                sleep(0.5)
                count += 1
        else:
            break
    delete_all_messages()
    send_message(f"{count} Download(s) has been Cancelled!", context.bot, update)


cancel_mirror_handler = CommandHandler(
    BotCommands.CancelMirror,
    cancel_mirror,
    filters=(CustomFilters.authorized_chat | CustomFilters.authorized_user)
    & CustomFilters.mirror_owner_filter
    | CustomFilters.sudo_user,
    run_async=True,
)
cancel_all_handler = CommandHandler(
    BotCommands.CancelAllCommand,
    cancel_all,
    filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
    run_async=True,
)
dispatcher.add_handler(cancel_all_handler)
dispatcher.add_handler(cancel_mirror_handler)
