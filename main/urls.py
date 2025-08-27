from django.urls import path

from main.views import *



urlpatterns = [
    
#pages
    path('classes/', classes, name='classes'),
    path('courses/', courses, name='courses'),
    path('forum/', forum, name='forum'),
    path('games/', games, name='games'),
    path('', index, name='index'),
    path('login/', login_page, name='login'),
    path('profiles/', profiles, name='profiles'),

# API endpoints
    path("api/auth/register", api_register, name="api_register"),
    path("api/auth/login", api_login, name="api_login"),
    path("api/auth/logout", api_logout, name="api_logout"),
    path("api/me", api_me, name="api_me"),
    path("login/", login_page, name="login"),
   


    # games API
     path("games/", games, name="games"),

    # Games API (trailing slashes to match your JS)
    path("api/games/", api_games_list, name="api_games_list"),
    path("api/games/<int:pk>/", api_game_detail, name="api_game_detail"),
    path("api/games/<int:pk>/submit/", api_game_submit, name="api_game_submit"),

    #courses API
    
    path("api/courses/", api_courses, name="api_courses"),
    #API classes
    path("api/classes", api_classes_list, name="api_classes_list"),
    # same path for POST (reserve) and DELETE (unreserve) — handled by method inside the view
    path("api/classes/<int:pk>/reserve", api_class_reserve, name="api_class_reserve"),
    path("api/me/classes", api_me_classes, name="api_me_classes"),

    #forum.py
    path("api/forum/categories", api_forum_categories, name="api_forum_categories"),
    path("api/forum/threads", api_forum_threads, name="api_forum_threads"),
    path("api/forum/threads/<slug:slug>", api_forum_thread_detail, name="api_forum_thread_detail"),
    path("api/forum/threads/<slug:slug>/posts", api_forum_thread_posts, name="api_forum_thread_posts"),
    path("api/forum/posts/<int:post_id>/like", api_forum_post_like, name="api_forum_post_like"),

]




    
   