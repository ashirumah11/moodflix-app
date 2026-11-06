from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.mood_selection_view, name='mood_selection'),
    path('<slug:mood_slug>/', views.mood_results_view, name='mood_results'),
]

