from django.urls import path
from .views import feed_view
from . import views
app_name = 'feed'
urlpatterns = [
    path('', feed_view, name='index'),
    path('problem/<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('problem/<int:problem_id>/submit/', views.submit_solution, name='submit_solution'),
]
