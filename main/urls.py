# main/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# ✅ Page handlers now come from pages.py (renamed from views.py)
# AFTER
from main.views import (
    index as index_page,
    classes as classes_page,
    courses as courses_page,
    resources as resources_page,
    forum as forum_page,
    games as games_page,
    add_question as add_question_page,
    profiles as profiles_page,
    survey_builder,
    survey_analytics_dashboard,




    # game APIs
    api_games_list,
    api_game_detail,
    api_game_submit,
    api_game_questions_manage,
    api_game_add_question,
    api_surveys_collection,
    api_survey_detail,
    api_survey_questions,
    api_survey_question_detail,
    api_survey_next,
    api_survey_participation,
    api_survey_responses,
    api_survey_analytics,
)

from main.views.game import api_game_question_manage
from main.views.index import (resources as resources_page)


# ✅ Auth views (single source of truth)
from .views import auth as auth_views

# Tutors / classes list
from main.views.tutorspage import (
    Tutors,
    api__list as api_classes_list,
    api_class_reserve,
    api_class_unreserve,
    api_me_classes,
)

# Tutor classes management
from main.views.classes import (
    api_tutor_classes,
    api_tutor_class_detail,
    api_tutor_payment_requests,
    api_tutor_payment_request_detail,
)

# Courses / Resources APIs
from main.views.courses import (
    tutor_admin,
    api_tutor_courses,
    api_tutor_course_detail,
    api_tutor_course_add_resource,
    api_tutor_resource_detail,
    api_tutor_course_thumbnail,
    api_tutor_course_reorder,
    api_course_sequence,
    api_course_poll_vote,
    api_courses,
)
from main.views.resources import api_resources_library

# Messages
from main.views.messages import (
    api_messages_list,
    api_messages_create,
    api_messages_read,
    api_messages_recipients,
    messages_page,
)

# Tutor session workflow
from main.views.tutor import (
    tutor_dashboard,
    book_session,
    confirm_session,
    video_session,
    complete_session,
    cancel_session,
)

# Chatbot
from main.views.chatbotview import (
    chatbot_api,
    internet_search_api,
    chatbot_history_api,
)

# Forum APIs
from main.views.forum import (
    api_forum_categories,
    api_forum_threads,
    api_forum_thread_detail,
    api_forum_thread_posts,
    api_forum_post_like,
)

# Admin UI (custom)
from main.views.adminui import (
    admin_users_page,
    api_admin_users,
    api_admin_user_update,
    admin_approvals_page,
    api_admin_content_pending,
    api_admin_course_approve,
    api_admin_game_approve,
    admin_dashboard_page,
    administrator_login_page,
    admin_resources_page,
    api_admin_resource_categories,
    api_admin_resource_category_detail,
    api_admin_resource_documents,
    api_admin_resource_upload,
    api_admin_resource_document_detail,
    api_admin_chatbot_config,
    admin_tutor_applications_page,
    api_admin_tutor_applications,
    api_admin_tutor_application_detail,
)

urlpatterns = [
    # ---------- Root ----------
    path("", auth_views.login_page, name="root_login"),

    # ---------- Pages ----------
    path("index/",        index_page,          name="index"),
    path("classes/",      classes_page,        name="classes"),
    path("Tutors/",       Tutors,              name="Tutors"),
    path("courses/",      courses_page,        name="courses"),
    path("resources/",    resources_page,      name="resources"),
    path("forum/",        forum_page,          name="forum"),
    path("games/",        games_page,          name="games"),
    path("games/add/",    add_question_page,   name="add_question"),
    path("profiles/",     profiles_page,       name="profiles"),
    path("surveys/builder/",   survey_builder,             name="survey_builder"),
    path("surveys/analytics/", survey_analytics_dashboard, name="survey_analytics_dashboard"),
    path("awaiting-activation/",              auth_views.awaiting_activation_page,  name="awaiting_activation"),

    # ---------- Auth ----------
    path("login/",                        auth_views.login_page,          name="login"),
    path("api/auth/login",                auth_views.api_login,           name="api_login"),
    path("api/auth/register",             auth_views.api_register,        name="api_register"),
    path("api/auth/logout",               auth_views.api_logout,          name="api_logout"),
    path("api/me",                        auth_views.api_me,              name="api_me"),
    path("api/me/delete",                 auth_views.api_delete_account,  name="api_delete_account"),
    path("api/me/avatar",                 auth_views.api_upload_avatar,   name="api_upload_avatar"),
    path("change-password/",              auth_views.change_password_page, name="change_password"),
    path("api/auth/change-password",      auth_views.api_change_password,  name="api_change_password"),
    path("forgot-password/",              auth_views.forgot_password_page, name="forgot_password"),
    path("api/auth/forgot-password",      auth_views.api_forgot_password,  name="api_forgot_password"),
    path("reset-password/<str:uidb64>/<str:token>/",
                                         auth_views.reset_password_page,  name="reset_password"),
    path("api/auth/reset-password",      auth_views.api_reset_password,   name="api_reset_password"),

    # ---------- Games API ----------
    path("api/games/",                     api_games_list,        name="api_games_list"),
    path("api/games/<int:pk>/",            api_game_detail,       name="api_game_detail"),
    path("api/games/<int:pk>/submit/",     api_game_submit,       name="api_game_submit"),
    path("api/games/<int:pk>/questions/",  api_game_add_question, name="api_game_add_question"),
    path("api/games/<int:pk>/questions/manage/",              api_game_questions_manage,    name="api_game_questions_manage"),

    path("api/games/<int:pk>/questions/<int:question_id>/manage/", api_game_question_manage, name="api_game_question_manage"),
    # ---------- Surveys ----------
    path("api/surveys/",                                api_surveys_collection,     name="api_surveys_collection"),
    path("api/surveys/next/",                           api_survey_next,            name="api_survey_next"),
    path("api/surveys/<int:pk>/questions/",             api_survey_questions,       name="api_survey_questions"),
    path("api/surveys/<int:pk>/questions/<int:question_id>/", api_survey_question_detail, name="api_survey_question_detail"),
    path("api/surveys/<int:pk>/participation/",         api_survey_participation,   name="api_survey_participation"),
    path("api/surveys/<int:pk>/responses/",             api_survey_responses,       name="api_survey_responses"),
    path("api/surveys/<int:pk>/analytics/",             api_survey_analytics,       name="api_survey_analytics"),
    path("api/surveys/<int:pk>/",                       api_survey_detail,          name="api_survey_detail"),

    # ---------- Courses / Resources ----------
    path("api/courses/",                               api_courses,                 name="api_courses"),
    path("api/resources/library",                      api_resources_library,       name="api_resources_library"),
    path("tutor/admin/",                               tutor_admin,                 name="tutor_admin"),
    path("api/tutor/courses",                          api_tutor_courses,           name="api_tutor_courses"),
    path("api/tutor/courses/<int:pk>",                 api_tutor_course_detail,     name="api_tutor_course_detail"),
    path("api/tutor/courses/<int:pk>/resources",       api_tutor_course_add_resource, name="api_tutor_course_add_resource"),
    path("api/tutor/resources/<int:res_id>",           api_tutor_resource_detail,   name="api_tutor_resource_detail"),
    path("api/tutor/courses/<int:pk>/thumbnail",       api_tutor_course_thumbnail,  name="api_tutor_course_thumbnail"),
    path("api/tutor/courses/<int:pk>/reorder",         api_tutor_course_reorder,    name="api_tutor_course_reorder"),
    path("api/courses/<int:pk>/sequence",              api_course_sequence,         name="api_course_sequence"),
    path("api/courses/<int:pk>/resources/<int:res_id>/poll/vote",
                                                      api_course_poll_vote,         name="api_course_poll_vote"),

    # ---------- Classes ----------
    path("api/classes",                         api_classes_list,        name="api_classes_list"),
    path("api/classes/<int:pk>/reserve",        api_class_reserve,       name="api_class_reserve"),
    path("api/classes/<int:pk>/unreserve",      api_class_unreserve,     name="api_class_unreserve"),
    path("api/me/classes",                      api_me_classes,          name="api_me_classes"),
    path("api/tutor/classes",                   api_tutor_classes,       name="api_tutor_classes"),
    path("api/tutor/classes/<int:pk>",          api_tutor_class_detail,  name="api_tutor_class_detail"),
    path("api/tutor/payment-requests",          api_tutor_payment_requests, name="api_tutor_payment_requests"),
    path("api/tutor/payment-requests/<int:pk>", api_tutor_payment_request_detail, name="api_tutor_payment_request_detail"),

    # ---------- Messages ----------
    path("api/messages",                        api_messages_list,       name="api_messages_list"),
    path("api/messages/send",                   api_messages_create,     name="api_messages_create"),
    path("api/messages/<int:pk>/read",          api_messages_read,       name="api_messages_read"),
    path("api/messages/recipients",             api_messages_recipients, name="api_messages_recipients"),
    path("messages/",                           messages_page,           name="messages_page"),

    # ---------- Chatbot ----------
    path("api/chatbot/",                        chatbot_api,             name="chatbot_api"),
    path("api/chatbot/search/",                 internet_search_api,     name="chatbot_search"),
    path("api/chatbot/history/",                chatbot_history_api,     name="chatbot_history"),

    #-----Forum Critical Api's-----------
    path("api/forum/categories", api_forum_categories, name="api_forum_categories"),
    path("api/forum/threads", api_forum_threads, name="api_forum_threads"),
    path("api/forum/threads/<slug:slug>", api_forum_thread_detail, name="api_forum_thread_detail"),
    path("api/forum/threads/<slug:slug>/posts", api_forum_thread_posts, name="api_forum_thread_posts"),
    path("api/forum/posts/<int:post_id>/like", api_forum_post_like, name="api_forum_post_like"),

    # ---------- Tutor Sessions ----------
    path("session/<int:session_id>/confirm/",   confirm_session,         name="confirm_session"),
    path("session/<int:session_id>/video/",     video_session,           name="video_session"),
    path("session/<int:session_id>/complete/",  complete_session,        name="complete_session"),
    path("session/<int:session_id>/cancel/",    cancel_session,          name="cancel_session"),
    path("tutor/dashboard/",                    tutor_dashboard,         name="tutor_dashboard"),
    path("tutor/book/<int:class_id>/",          book_session,            name="book_session"),

    # ---------- Admin UI ----------
    path("administrator/login/",                administrator_login_page,            name="administrator_login"),
    path("administrator/",                      admin_dashboard_page,                name="administrator_dashboard"),
    path("administrator/users/",                admin_users_page,                    name="administrator_users_page"),
    path("administrator/approvals/",            admin_approvals_page,                name="administrator_approvals_page"),
    path("administrator/resources/",            admin_resources_page,                name="administrator_resources_page"),
    path("administrator/tutor-applications/",   admin_tutor_applications_page,       name="administrator_tutor_applications_page"),
    path("api/admin/resource-categories",       api_admin_resource_categories,       name="api_admin_resource_categories"),
    path("api/admin/resource-categories/<int:pk>",
                                              api_admin_resource_category_detail,    name="api_admin_resource_category_detail"),
    path("api/admin/resource-documents",        api_admin_resource_documents,        name="api_admin_resource_documents"),
    path("api/admin/resource-documents/<int:pk>",
                                              api_admin_resource_document_detail,    name="api_admin_resource_document_detail"),
    path("api/admin/resource-upload",           api_admin_resource_upload,           name="api_admin_resource_upload"),
    path("api/admin/chatbot-config",            api_admin_chatbot_config,            name="api_admin_chatbot_config"),
    path("api/admin/tutor-applications/",       api_admin_tutor_applications,        name="api_admin_tutor_applications"),
    path("api/admin/tutor-applications/<int:pk>/",
                                              api_admin_tutor_application_detail,   name="api_admin_tutor_application_detail"),
    path("api/admin/users",                     api_admin_users,                     name="api_admin_users"),
    path("api/admin/users/<int:pk>",            api_admin_user_update,               name="api_admin_user_update"),
    path("api/admin/content/pending",           api_admin_content_pending,           name="api_admin_content_pending"),
    path("api/admin/courses/<int:pk>/approve",  api_admin_course_approve,            name="api_admin_course_approve"),
    path("api/admin/games/<int:pk>/approve",    api_admin_game_approve,              name="api_admin_game_approve"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
