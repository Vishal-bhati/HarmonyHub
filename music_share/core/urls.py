from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_room, name='create_room'),
    path('join/', views.join_room, name='join_room'),
    path('room/<str:code>/', views.room, name='room'),
    
    # Spotify OAuth routes
    path('spotify/login/', views.spotify_login, name='spotify_login'),
    path('spotify/redirect/', views.spotify_callback, name='spotify_callback'),
    path('room/<str:code>/dedicate/', views.dedicate_song, name='dedicate_song'),
    path('spotify/search/', views.search_spotify, name='search_spotify'),
    path('spotify/logout/', views.spotify_logout, name='logout_spotify'),
    path('room/<str:code>/live-dedications/', views.get_latest_dedications, name='live_dedications'),
    path('spotify/current/', views.current_song_api, name='current_song_api'),
    path('spotify/lyrics/', views.get_lyrics, name='get_lyrics'),

]
