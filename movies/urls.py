from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('discover/', views.discover_view, name='discover'),
    path('trending/', views.trending_view, name='trending'),
    path('search/', views.search_view, name='search'),
    path('movie/<int:tmdb_id>/', views.movie_detail_view, name='movie_detail'),
    path('tv/<int:tmdb_id>/', views.tv_detail_view, name='tv_detail'),
    path('trailer/<str:media_type>/<int:tmdb_id>/', views.movie_trailer_view, name='movie_trailer'),
]
