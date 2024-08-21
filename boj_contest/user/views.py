# user/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('feed:index')  # 로그인 후 리디렉션할 페이지
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'user/login.html')

def user_logout(request):
    logout(request)
    return redirect('user:login')

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully')
            return redirect('user:login')
    else:
        form = UserCreationForm()
    return render(request, 'user/register.html', {'form': form})
