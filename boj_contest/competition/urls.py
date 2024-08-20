# competition/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_participant, name='register'),
    path('submit/', views.submit_solution, name='submit'),
    path('results/', views.contest_results, name='results'),
    path('update/', views.update_problems, name='update_problems'),
]
