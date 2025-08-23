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

    #games
    path("games/", games, name="games"),

    # games API
    path("api/games", api_games_list, name="api_games_list"),
    path("api/games/<slug:slug>", api_game_detail, name="api_game_detail"),
]



