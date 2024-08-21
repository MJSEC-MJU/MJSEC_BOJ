"""
URL configuration for boj_contest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# contest/urls.py
from django.contrib import admin
from django.urls import path, include
from competition.views import redirect_based_on_login
urlpatterns = [
    path('', redirect_based_on_login, name='redirect_based_on_login'),
    path('admin/', admin.site.urls),
    path('competition/', include('competition.urls')),
    path('feed/', include('feed.urls')),
    path('user/', include('user.urls'))
    
    
]
