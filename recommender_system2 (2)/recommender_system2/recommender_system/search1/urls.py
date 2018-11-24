from django.contrib import admin
from django.urls import path
from .views import find_results1
from . import views
urlpatterns = [
    path('', views.show_form),
    path('getquery/', views.get_data),
]
find_results1(repeat_until=None)