from django.urls import path
from . import views
from . import auth_views

app_name = 'Market'

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    
    # Аутентификация
    path('login/', auth_views.user_login, name='login'),
    path('register/', auth_views.user_register, name='register'),
    path('logout/', auth_views.user_logout, name='logout'),
    path('profile/', auth_views.profile, name='profile'),
    

]