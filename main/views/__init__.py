# stem_app/views/__init__.py
from .index import index
from .login import login_page, api_me, api_login, api_logout, api_register
from .profiles import profiles
from .game import games, api_games_list, api_game_detail
from .courses import courses
from .classes import classes
from .forum import forum

__all__ = [
    "index",
    "login_page",
    "api_me",
    "api_login",
    "api_logout",
    "api_register",
    "profiles",
    "games",
    "api_games_list",
    "api_game_detail",
    "courses",
    "classes",
    "forum",
]
