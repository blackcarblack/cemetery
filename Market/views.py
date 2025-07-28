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

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('Market:index')
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, "Market/login.html", {'form': form})

def admin_register(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Admin account created successfully!')
            return redirect('Market:login')
    else:
        form = AdminRegistrationForm()
    return render(request, "Market/admin_register.html", {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('Market:index')

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('Market:admin_products')
    else:
        form = ProductForm()
    return render(request, "Market/add_product.html", {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('Market:admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, "Market/update_product.html", {'form': form, 'product': product})

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('Market:admin_products')
    return render(request, "Market/delete_product.html", {'product': product})

@csrf_exempt
def rate_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        user_ip = request.META.get('REMOTE_ADDR')
        is_like = request.POST.get('is_like') == 'true'
        
        # Check if user already rated this product
        existing_rating = ProductRating.objects.filter(product=product, user_ip=user_ip).first()
        if existing_rating:
            existing_rating.is_like = is_like
            existing_rating.save()
        else:
            ProductRating.objects.create(product=product, user_ip=user_ip, is_like=is_like)
        
        return JsonResponse({
            'likes': product.likes_count,
            'dislikes': product.dislikes_count,
            'rating_score': product.rating_score
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

def test(request):
    return render(request, "Market/test.html")

def sendgrid_email(request):
    if request.method == 'POST':
        try:
            send_mail(
                'Test Email',
                'This is a test email from Django.',
                settings.DEFAULT_FROM_EMAIL,
                ['test@example.com'],
                fail_silently=False,
            )
            messages.success(request, 'Email sent successfully!')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')
    return render(request, "Market/sendgrid_email.html")

def test_massegas(request):
    messages.success(request, 'This is a success message!')
    messages.error(request, 'This is an error message!')
    messages.warning(request, 'This is a warning message!')
    messages.info(request, 'This is an info message!')
    return render(request, "Market/test_messages.html")

@csrf_exempt
def click_counter(request):
    if request.method == 'POST':
        # Simple click counter implementation
        current_count = request.session.get('click_count', 0)
        request.session['click_count'] = current_count + 1
        return JsonResponse({'count': request.session['click_count']})
    return JsonResponse({'count': request.session.get('click_count', 0)})

@csrf_exempt
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        user = request.user if request.user.is_authenticated else None
        
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        return JsonResponse({'message': 'Product added to cart', 'quantity': cart_item.quantity})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_cart(request):
    cart_data = []
    total_price = 0
    
    if request.user.is_authenticated:
        # For authenticated users, use database cart
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            item_total = item.product.price * item.quantity
            total_price += item_total
            cart_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_price': float(item.product.price),
                'quantity': item.quantity,
                'total': float(item_total)
            })
    else:
        # For anonymous users, use session-based cart
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                item_total = product.price * quantity
                total_price += item_total
                cart_data.append({
                    'id': f'session_{product_id}',
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_price': float(product.price),
                    'quantity': quantity,
                    'total': float(item_total)
                })
            except Product.DoesNotExist:
                # Remove invalid product from session cart
                continue
    
    return JsonResponse({
        'cart_items': cart_data,
        'total_price': float(total_price),
        'count': len(cart_data)
    })

@csrf_exempt
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = get_object_or_404(Cart, user=user, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({'message': 'Cart updated', 'quantity': cart_item.quantity})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        cart_item = get_object_or_404(Cart, user=user, product_id=product_id)
        cart_item.delete()
        
        return JsonResponse({'message': 'Product removed from cart'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "Market/admin_products.html", {'page_obj': page_obj})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_users = CustomUser.objects.count()
    total_ratings = ProductRating.objects.count()
    
    # Get recent products
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    # Get rating statistics
    rating_stats = ProductRating.objects.aggregate(
        likes=Count(Case(When(is_like=True, then=1), output_field=IntegerField())),
        dislikes=Count(Case(When(is_like=False, then=1), output_field=IntegerField()))
    )
    
    context = {
        'total_products': total_products,
        'total_users': total_users,
        'total_ratings': total_ratings,
        'recent_products': recent_products,
        'rating_stats': rating_stats,
    }
    
    return render(request, "Market/admin_dashboard.html", context)

def get_doom_captcha(request):
    captcha = DoomCaptcha()
    img_io, code = captcha.get_captcha()
    
    # Store code in session for verification
    request.session['doom_captcha_code'] = code
    
    response = HttpResponse(img_io.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

@csrf_exempt
def verify_doom_captcha(request):
    if request.method == 'POST':
        user_input = request.POST.get('captcha', '').strip()
        stored_code = request.session.get('doom_captcha_code', '')
        
        captcha = DoomCaptcha()
        is_valid = captcha.validate_captcha(user_input, stored_code)
        
        if is_valid:
            request.session['doom_captcha_passed'] = True
            return JsonResponse({'valid': True, 'message': 'CAPTCHA verified successfully!'})
        else:
            return JsonResponse({'valid': False, 'message': 'Invalid CAPTCHA. Please try again.'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def test_doom_captcha(request):
    return render(request, "Market/test_doom_captcha.html")
