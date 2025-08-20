from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import UserRegistrationForm, LoginForm
from .doom_captcha import DoomCaptcha


def user_login(request):
    if request.user.is_authenticated:
        return redirect('Market:index')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Вітаємо, {user.username}! Ви успішно увійшли в систему.')
                return redirect('Market:index')
            else:
                messages.error(request, 'Невірний логін або пароль.')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = LoginForm()
    
    return render(request, 'Market/auth/login.html', {
        'form': form,
        'title': 'Вхід до системи'
    })


def user_register(request):
    if request.user.is_authenticated:
        return redirect('Market:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        doom_completed = request.POST.get('doom_completed', 'false').lower() == 'true'
        doom_session = request.POST.get('doom_session', '')
        
        if not validate_doom_captcha(doom_completed, doom_session, request):
            messages.error(request, '🎮 DOOM CAPTCHA не пройдена! Вбийте 3 монстри в справжній грі DOOM 1993!')
            form.add_error(None, 'Потрібно пройти DOOM CAPTCHA')
        elif form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'🎉 Вітаємо, {user.username}! Ви успішно пройшли DOOM CAPTCHA і створили аккаунт!')
                return redirect('Market:index')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'Market/auth/register.html', {
        'form': form,
        'title': 'Реєстрація'
    })


def validate_doom_captcha(doom_completed, doom_session, request):
    from django.core.cache import cache
    
    if not doom_completed or not doom_session:
        return False
    
    if len(doom_session) < 5:
        return False
    
    cache_key = f'doom_session_used_{doom_session}'
    if cache.get(cache_key):
        return False
    
    cache.set(cache_key, True, 3600)
    
    return True


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def user_logout(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'До побачення, {username}! Ви успішно вийшли з системи.')
    
    return redirect('Market:index')





@login_required
def profile(request):
    return render(request, 'Market/auth/profile.html', {
        'title': f'Профіль - {request.user.username}'
    })