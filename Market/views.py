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

def team_info(request):
    return render(request, "Market/team.html")

def site_info(request):
    return render(request, "Market/site_info.html")

def about(request):
    return render(request, "Market/about.html")

def team(request):
    return render(request, "Market/team.html")