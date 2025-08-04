from django.urls import path
from . import views
from . import auth_views
from django.contrib import admin
app_name = 'Market'

urlpatterns = [
    # �������� ��������
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    path('menu/', views.shop, name='menu'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),

    # ��������������
    path('login/', auth_views.user_login, name='login'),
    path('register/', auth_views.user_register, name='register'),
    path('logout/', auth_views.user_logout, name='logout'),
    path('profile/', auth_views.profile, name='profile'),

    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('admin/', admin.site.urls),
]