from html_telegraph_poster import TelegraphPoster


def post_to_telegraph(a_title: str, content: str) -> str:
    """Create a Telegram Post using HTML Content"""
    post_client = TelegraphPoster(use_api=True)
    auth_name = "mirrorbot"
    post_client.create_api_token(auth_name)
    post_page = post_client.post(
        title=a_title,
        author=auth_name,
        text=content,
    )
    return post_page["url"]
