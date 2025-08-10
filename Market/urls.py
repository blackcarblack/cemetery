from django.urls import path, include
from . import views
from . import auth_views
from django.contrib import admin
app_name = 'Market'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    path('menu/', views.shop, name='menu'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('captcha/', include('captcha.urls')),

    path('login/', auth_views.user_login, name='login'),
    path('register/', auth_views.user_register, name='register'),
    path('logout/', auth_views.user_logout, name='logout'),
    path('profile/', auth_views.profile, name='profile'),

    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('admin/', admin.site.urls),
    path('my-cart/', views.view_cart, name='user_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/add_one/<int:product_id>/', views.add_one_to_cart, name='add_one_to_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    # Bonus shop routes
    path('bonus-shop/', views.bonus_shop, name='bonus_shop'),
    path('buy-with-bonus/<int:product_id>/', views.buy_with_bonus, name='buy_with_bonus'),
    path('add-bonus-to-cart/<int:product_id>/', views.add_bonus_to_cart, name='add_bonus_to_cart'),
    path('remove-bonus-from-cart/<int:product_id>/', views.remove_bonus_from_cart, name='remove_bonus_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
]