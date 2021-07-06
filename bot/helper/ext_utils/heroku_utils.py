from functools import wraps

import heroku3

from bot import HEROKU_API_KEY, HEROKU_APP_NAME


# Preparing For Setting Config
# Implement by https://github.com/jusidama18 and Based on this https://github.com/DevsExpo/FridayUserbot/blob/master/plugins/heroku_helpers.py
def check_heroku(func):
    if HEROKU_API_KEY:
        heroku_client = heroku3.from_key(HEROKU_API_KEY)

    @wraps(func)
    async def heroku_cli(client, message):
        heroku_app = None
        if not heroku_client:
            await message.reply_text(
                "`Please Add HEROKU_API_KEY Key For This To Function To Work!`",
                parse_mode="markdown",
            )
        elif not HEROKU_APP_NAME:
            await message.reply_text(
                "`Please Add HEROKU_APP_NAME For This To Function To Work!`",
                parse_mode="markdown",
            )
        if HEROKU_APP_NAME and heroku_client:
            try:
                heroku_app = heroku_client.app(HEROKU_APP_NAME)
            except Exception:
                await message.reply_text(
                    message,
                    "`Heroku Api Key And App Name Doesn't Match!`",
                    parse_mode="markdown",
                )
            if heroku_app:
                await func(client, message, heroku_app)

    return heroku_cli


# Preparing For Update Bot
# Implement by https://github.com/jusidama18 and Based on this https://github.com/DevsExpo/FridayUserbot/blob/master/plugins/updater.py
def fetch_heroku_git_url():
    if not HEROKU_API_KEY:
        return None
    if not HEROKU_APP_NAME:
        return None
    heroku = heroku3.from_key(HEROKU_API_KEY)
    try:
        heroku_applications = heroku.apps()
    except Exception:
        return None
    heroku_app = None
    for app in heroku_applications:
        if app.name == HEROKU_APP_NAME:
            heroku_app = app
            break
    if not heroku_app:
        return None
    return heroku_app.git_url.replace("https://", "https://api:" + HEROKU_API_KEY + "@")
