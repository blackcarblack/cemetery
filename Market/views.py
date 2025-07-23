import datetime
import json
import os
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegistrationForm, AdminRegistrationForm, ProductForm, LoginForm
from .doom_captcha import DoomCaptcha
import base64
from io import BytesIO
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, ProductRating, Cart, CustomUser
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from datetime import timedelta
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Case, When, IntegerField

def index(request):
    return render(request, "Market/index.html")

def dishes(request):
    products = Product.objects.all()
    return render(request, "Market/dishes.html", {'products': products})

def team_info(request):
    return render(request, "Market/team.html")

def site_info(request):
    return render(request, "Market/site_info.html")

def add_dish_info(request):
    return render(request, "Market/add_dish_info.html")

def about(request):
    return render(request, "Market/about.html")

def about_me(request):
    return render(request, "Market/about_me.html")

def register(request):
    return render(request, "Market/register.html")

def admin_register(request):
    return render(request, "Market/admin_register.html")

def user_login(request):
    return render(request, "Market/login.html")

def user_logout(request):
    return render(request, "Market/logout.html")

def add_product(request):
    return render(request, "Market/add_product.html")

def update_product(request, pk):
    return render(request, "Market/update_product.html")

def delete_product(request, pk):
    return render(request, "Market/delete_product.html")

def rate_product(request, product_id):
    return render(request, "Market/rate_product.html")

def test(request):
    return render(request, "Market/test.html")

def sendgrid_email(request):
    return render(request, "Market/sendgrid_email.html")

def test_massegas(request):
    return render(request, "Market/test_messages.html")

def click_counter(request):
    return render(request, "Market/click_counter.html")

def add_to_cart(request, product_id):
    return render(request, "Market/add_to_cart.html")

def get_cart(request):
    return render(request, "Market/cart.html")

def update_cart_quantity(request, product_id):
    return render(request, "Market/update_cart.html")

def remove_from_cart(request, product_id):
    return render(request, "Market/remove_cart.html")

def admin_products(request):
    return render(request, "Market/admin_products.html")

def admin_dashboard(request):
    return render(request, "Market/admin_dashboard.html")

def get_doom_captcha(request):
    return render(request, "Market/doom_captcha.html")

def verify_doom_captcha(request):
    return render(request, "Market/verify_captcha.html")

def test_doom_captcha(request):
    return render(request, "Market/test_captcha.html")