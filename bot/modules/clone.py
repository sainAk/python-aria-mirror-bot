from telegram.ext import CommandHandler

from bot import CLONE_LIMIT, LOGGER, STOP_DUPLICATE_CLONE, dispatcher
from bot.helper.ext_utils.bot_utils import get_readable_file_size
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    delete_message,
    send_markup,
    send_message,
)


def cloneNode(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    if len(args) > 1:
        link = args[1]
        gd = GoogleDriveHelper()
        if CLONE_LIMIT is not None or STOP_DUPLICATE_CLONE:
            res, clonesize, name = gd.clonehelper(link)
            if res != "":
                send_message(res, context.bot, update)
                return
            if STOP_DUPLICATE_CLONE:
                LOGGER.info("Checking File/Folder if already in Drive...")
                smsg, button = gd.drive_list(name)
                if smsg:
                    msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                    send_markup(msg3, context.bot, update, button)
                    return
            if CLONE_LIMIT is not None:
                LOGGER.info("Checking File/Folder Size...")
                limit = CLONE_LIMIT
                limit = limit.split(" ", maxsplit=1)
                limitint = int(limit[0])
                msg2 = f"Failed, Clone limit is {CLONE_LIMIT}.\nYour File/Folder size is {get_readable_file_size(clonesize)}."
                if "G" in limit[1] or "g" in limit[1]:
                    if clonesize > limitint * 1024 ** 3:
                        send_message(msg2, context.bot, update)
                        return
                elif "T" in limit[1] or "t" in limit[1]:
                    if clonesize > limitint * 1024 ** 4:
                        send_message(msg2, context.bot, update)
                        return
        msg = send_message(f"Cloning: <code>{link}</code>", context.bot, update)
        result, button = gd.clone(link)
        delete_message(context.bot, msg)
        if button == "":
            send_message(result, context.bot, update)
        else:
            if update.message.from_user.username:
                uname = f"@{update.message.from_user.username}"
            else:
                uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            if uname is not None:
                cc = f"\n\ncc: {uname}"
            send_markup(result + cc, context.bot, update, button)
    else:
        send_message("Provide G-Drive Shareable Link to Clone.", context.bot, update)


clone_handler = CommandHandler(
    BotCommands.CloneCommand,
    cloneNode,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
dispatcher.add_handler(clone_handler)
