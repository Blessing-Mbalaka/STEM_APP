# stem_app/views/__init__.py
from .index import index
from .login import login_page, api_me, api_login, api_logout, api_register
from .profiles import profiles
from .game import games, api_games_list, api_game_detail, api_game_submit
from .courses import courses, api_courses
from .classes import classes, api_classes_list, api_class_reserve, api_class_unreserve, api_me_classes
from .forum import forum, api_forum_categories, api_forum_threads, api_forum_thread_detail, api_forum_thread_posts, api_forum_post_like



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
    "api_game_submit",
    "courses", "api_courses",
    "classes",
    "forum",
    "api_forum_categories",
    "api_forum_threads",
    "api_forum_thread_detail",
    "api_forum_thread_posts",
    "api_forum_post_like",
    "api_classes_list","api_class_reserve","api_class_unreserve","api_me_classes"
]


