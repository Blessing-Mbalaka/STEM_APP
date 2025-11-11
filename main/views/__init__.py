# stem_app/views/__init__.py
from .index import index, resources
from .login import login_page, api_me, api_login, api_logout, api_register
from .profiles import profiles
from .game import games, add_question, api_games_list, api_game_detail, api_game_submit, api_game_add_question, api_game_questions_manage, api_game_question_manage
from .courses import courses, api_courses
from .classes import classes, api_classes_list, api_class_reserve, api_class_unreserve, api_me_classes
from .forum import forum, api_forum_categories, api_forum_threads, api_forum_thread_detail, api_forum_thread_posts, api_forum_post_like
from .files import pdf_embed 
from .tutor import confirm_session, video_session, complete_session, tutor_dashboard, book_session, api_tutor_courses, api_tutor_course_detail, api_tutor_course_add_resource, api_tutor_course_thumbnail, api_tutor_course_reorder, tutor_admin  
from .surveys import (
    survey_builder,
    survey_analytics_dashboard,
    api_surveys_collection,
    api_survey_detail,
    api_survey_questions,
    api_survey_question_detail,
    api_survey_next,
    api_survey_participation,
    api_survey_responses,
    api_survey_analytics,
)
    

__all__ = [
    "index", "resources", "pdf_embed",
    "login_page",
    "api_me",
    "api_login",
    "api_logout",
    "api_register",
    "profiles",
    "games",
    "add_question",
    "api_games_list",
    "api_game_detail",
    "api_game_submit",
    "api_game_add_question",
    "api_game_questions_manage",
    "api_game_question_manage",
    "courses", "api_courses",
    "classes",
    "forum",
    "api_forum_categories",
    "api_forum_threads",
    "api_forum_thread_detail",
    "api_forum_thread_posts",
    "api_forum_post_like",
    "tutor_dashboard",
    "book_session", 
    "confirm_session",
    "video_session",
    "complete_session",
    "api_classes_list","api_class_reserve","api_class_unreserve","api_me_classes",
    "survey_builder",
    "survey_analytics_dashboard",
    "api_surveys_collection",
    "api_survey_detail",
    "api_survey_questions",
    "api_survey_question_detail",
    "api_survey_next",
    "api_survey_participation",
    "api_survey_responses",
    "api_survey_analytics",
]


