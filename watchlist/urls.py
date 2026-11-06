from django.urls import path
from . import views

app_name = 'watchlist'

urlpatterns = [
    path('', views.watchlist_index_view, name='index'),
    path('toggle/', views.watchlist_toggle_view, name='toggle'),
    path('toggle-watched/<int:item_id>/', views.watchlist_toggle_watched_view, name='toggle_watched'),
    path('remove/<int:item_id>/', views.watchlist_remove_view, name='remove'),
]

