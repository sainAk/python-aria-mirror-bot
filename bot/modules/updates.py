# Implement By https://github.com/jusidama18
# Based on this https://github.com/DevsExpo/FridayUserbot/blob/master/plugins/updater.py

import logging
import os
from subprocess import CalledProcessError, run
from sys import executable

from telegram.ext.commandhandler import CommandHandler

from bot import UPSTREAM_BRANCH, UPSTREAM_REPO, app
from bot.helper.ext_utils.fs_utils import clean_all
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import edit_message, send_message

LOGGER = logging.getLogger(__name__)


def update(update, context):
    reply = send_message("Updating... Please wait!", context.bot, update)
    try:
        with open(".restartmsg", "w") as f:
            f.truncate(0)
            f.write(f"{reply.chat.id}\n{reply.message_id}\n")
        run("rm -rf /usr/src/app/repo", shell=True, check=True)
        edit_message("Cloning repo...", reply)
        shell = run(
            f"git clone --depth 1 --single-branch --branch {UPSTREAM_BRANCH} {UPSTREAM_REPO} /usr/src/app/repo",
            shell=True,
            check=True,
        )
        edit_message("Applying changes...", reply)
        run("cp -r /usr/src/app/repo/. /usr/src/app", shell=True, check=True)
        run("rm -rf /usr/src/app/repo/.git", shell=True, check=True)
        run("pip install -r /usr/src/app/requirements.txt", shell=True, check=True)
        clean_all()
        os.execl(executable, executable, "-m", "bot")
    except CalledProcessError as e:
        edit_message(f"Update failed\n <code>{e.output}</code>", reply)


restart_handler = CommandHandler(
    BotCommands.RestartCommand,
    update,
    filters=CustomFilters.owner_filter,
    run_async=True,
)
