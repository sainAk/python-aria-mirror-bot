from telegram.ext import CommandHandler

from bot import AUTHORIZED_CHATS, SUDO_USERS, dispatcher
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import send_message


def authorize(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        chat_id = int(message_[1])
        if chat_id not in AUTHORIZED_CHATS:
            msg = DbManger().db_auth(chat_id)
        else:
            msg = f"User already authorized: <code>{chat_id}</code>"
    else:
        if reply_message is None:
            # Trying to authorize a chat
            chat_id = update.effective_chat.id
            if chat_id not in AUTHORIZED_CHATS:
                msg = DbManger().db_auth(chat_id)
            else:
                msg = f"Already authorized chat: <code>{chat_id}</code>"

        else:
            # Trying to authorize someone in specific
            user_id = reply_message.from_user.id
            if user_id not in AUTHORIZED_CHATS:
                msg = DbManger().db_auth(user_id)
            else:
                msg = f"User already authorized: <code>{user_id}</code>"
    send_message(msg, context.bot, update)


def unauthorize(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        chat_id = int(message_[1])
        if chat_id in AUTHORIZED_CHATS:
            msg = DbManger().db_unauth(chat_id)
        else:
            msg = "User already unauthorized"
    else:
        if reply_message is None:
            # Trying to unauthorize a chat
            chat_id = update.effective_chat.id
            if chat_id in AUTHORIZED_CHATS:
                msg = DbManger().db_unauth(chat_id)
            else:
                msg = "Already unauthorized chat"
        else:
            # Trying to authorize someone in specific
            user_id = reply_message.from_user.id
            if user_id in AUTHORIZED_CHATS:
                msg = DbManger().db_unauth(user_id)
            else:
                msg = "User already unauthorized"
    send_message(msg, context.bot, update)


def add_sudo(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        chat_id = int(message_[1])
        if chat_id not in SUDO_USERS:
            msg = DbManger().db_addsudo(chat_id)
        else:
            msg = "Already Sudo"
    else:
        if reply_message is None:
            msg = "Give ID or Reply To message of whom you want to Promote"
        else:
            # Trying to authorize someone in specific
            user_id = reply_message.from_user.id
            if user_id not in SUDO_USERS:
                msg = DbManger().db_addsudo(user_id)
            else:
                msg = "Already Sudo"
    send_message(msg, context.bot, update)


def remove_sudo(update, context):
    reply_message = None
    message_ = None
    reply_message = update.message.reply_to_message
    message_ = update.message.text.split(" ")
    if len(message_) == 2:
        chat_id = int(message_[1])
        if chat_id in SUDO_USERS:
            msg = DbManger().db_rmsudo(chat_id)
        else:
            msg = "Not a Sudo"
    else:
        if reply_message is None:
            msg = "Give ID or Reply To message of whom you want to remove from Sudo"
        else:
            user_id = reply_message.from_user.id
            if user_id in SUDO_USERS:
                msg = DbManger().db_rmsudo(user_id)
            else:
                msg = "Not a Sudo"
    send_message(msg, context.bot, update)


def send_auth_chats(update, context):
    user = sudo = ""
    user += "\n".join(str(id) for id in AUTHORIZED_CHATS)
    sudo += "\n".join(str(id) for id in SUDO_USERS)
    send_message(
        f"<b><u>Authorized Chats</u></b>\n{user}\n<b><u>Sudo Users</u></b>\n{sudo}",
        context.bot,
        update,
    )


send_auth_handler = CommandHandler(
    command=BotCommands.AuthorizedUsersCommand,
    callback=send_auth_chats,
    filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
    run_async=True,
)
authorize_handler = CommandHandler(
    command=BotCommands.AuthorizeCommand,
    callback=authorize,
    filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
    run_async=True,
)
unauthorize_handler = CommandHandler(
    command=BotCommands.UnAuthorizeCommand,
    callback=unauthorize,
    filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
    run_async=True,
)
addsudo_handler = CommandHandler(
    command=BotCommands.AddSudoCommand,
    callback=add_sudo,
    filters=CustomFilters.owner_filter,
    run_async=True,
)
removesudo_handler = CommandHandler(
    command=BotCommands.RmSudoCommand,
    callback=remove_sudo,
    filters=CustomFilters.owner_filter,
    run_async=True,
)

dispatcher.add_handler(send_auth_handler)
dispatcher.add_handler(authorize_handler)
dispatcher.add_handler(unauthorize_handler)
dispatcher.add_handler(addsudo_handler)
dispatcher.add_handler(removesudo_handler)
