from django.urls import path
from . import views

app_name = 'Market'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('about_me/', views.about_me, name='about_me'),
    path('register/', views.register, name='register'),
    path('admin-register/', views.admin_register, name='admin_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('add-product/', views.add_product, name='add_product'),
    path('update/<int:pk>/', views.update_product, name='update_product'),
    path('delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('rate-product/<int:product_id>/', views.rate_product, name='rate_product'),
    path('test/', views.test, name='test'),
    path('sendgrid-email/', views.sendgrid_email, name='sendgrid_email'),
    path('test-messages/', views.test_massegas, name='test_messages'),
    path('click-counter/', views.click_counter, name='click_counter'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('get-cart/', views.get_cart, name='get_cart'),
    path('update-cart/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    # DOOM CAPTCHA URLs
    path('captcha/image/', views.get_doom_captcha, name='doom_captcha_image'),
    path('captcha/verify/', views.verify_doom_captcha, name='verify_doom_captcha'),
    path('doom-captcha-test/', views.test_doom_captcha, name='doom_captcha_test'),
]