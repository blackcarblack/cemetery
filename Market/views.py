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


def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    return user.is_authenticated and user.is_staff


def register(request):
    if request.user.is_authenticated:
        return redirect('Market:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Реєстрація успішна! Тепер ви можете увійти.')
            return redirect('Market:login')
        else:
            messages.error(request, 'Помилка при реєстрації. Перевірте введені дані.')
    else:
        form = UserRegistrationForm()
    return render(request, 'Market/registration.html', {'form': form})


@user_passes_test(is_admin)
def admin_register(request):
    """Реєстрація нових адміністраторів - доступна тільки існуючим адміністраторам"""
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            admin = form.save(commit=False)
            admin.set_password(form.cleaned_data['password'])
            admin.save()
            messages.success(request, f'Адміністратор {admin.username} успішно створений!')
            return redirect('Market:admin_products')
        else:
            messages.error(request, 'Помилка при створенні адміністратора.')
    else:
        form = AdminRegistrationForm()
    return render(request, 'Market/admin_registration.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('Market:index')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Вітаємо, {user.username}!')
                
                # Перенаправляем админов на админскую панель
                if user.is_staff:
                    return redirect('Market:admin_dashboard')
                
                # Перенаправляем обычных пользователей на главную
                next_url = request.GET.get('next', 'Market:index')
                return redirect(next_url)
            else:
                messages.error(request, 'Невірне ім\'я користувача або пароль.')
        else:
            messages.error(request, 'Помилка авторизації. Перевірте дані.')
    else:
        form = LoginForm()
    
    return render(request, 'Market/login.html', {'form': form})


def user_logout(request):
    """Вихід з системи"""
    logout(request)
    messages.success(request, 'Ви успішно вийшли з системи.')
    return redirect('Market:index')


def get_doom_captcha(request):
    """Generate and return a DOOM-style CAPTCHA image"""
    captcha = DoomCaptcha()
    img_io, code = captcha.get_captcha()
    
    # Store the CAPTCHA code in the session
    request.session['captcha_code'] = code
    
    # Return the image as a response
    return HttpResponse(img_io.getvalue(), content_type='image/png')


def verify_doom_captcha(request):
    """Verify the user's CAPTCHA input"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_input = request.POST.get('captcha_input', '').strip().upper()
        captcha_code = request.session.get('captcha_code', '')
        
        captcha = DoomCaptcha()
        is_valid = captcha.validate_captcha(user_input, captcha_code)
        
        # Clear the CAPTCHA code after verification
        if 'captcha_code' in request.session:
            del request.session['captcha_code']
        
        return JsonResponse({'valid': is_valid})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def test_doom_captcha(request):
    """Test page for the DOOM CAPTCHA"""
    return render(request, 'Market/doom_captcha_test.html')

@login_required
@user_passes_test(is_admin)
def add_product(request):
    """Додавання товару - доступно тільки адміністраторам"""
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успішно додано!')
            return redirect("Market:admin_products")
        else:
            messages.error(request, 'Помилка при додаванні товару.')
    else:
        form = ProductForm()
    return render(request, "Market/admin_add_product.html", {"form": form})


@login_required
def about_me(request):
    """Профіль користувача - доступно тільки авторизованим"""
    return render(request, "Market/about_me.html", {'user': request.user})
def about(request):
    return render(request, "Market/about.html")

def index(request):
    cutoff = timezone.now() - timedelta(hours=2)

    # Аннотируем товары с количеством лайков и дизлайков
    new_products = Product.objects.filter(created_at__gte=cutoff).annotate(
        annotated_likes_count=Count(Case(When(productrating__is_like=True, then=1), output_field=IntegerField())),
        annotated_dislikes_count=Count(Case(When(productrating__is_like=False, then=1), output_field=IntegerField())),
        annotated_rating_score=Count(Case(When(productrating__is_like=True, then=1), output_field=IntegerField())) -
                    Count(Case(When(productrating__is_like=False, then=1), output_field=IntegerField()))
    ).order_by('-annotated_rating_score', '-created_at')

    other_products = Product.objects.filter(created_at__lt=cutoff).annotate(
        annotated_likes_count=Count(Case(When(productrating__is_like=True, then=1), output_field=IntegerField())),
        annotated_dislikes_count=Count(Case(When(productrating__is_like=False, then=1), output_field=IntegerField())),
        annotated_rating_score=Count(Case(When(productrating__is_like=True, then=1), output_field=IntegerField())) -
                    Count(Case(When(productrating__is_like=False, then=1), output_field=IntegerField()))
    ).order_by('-annotated_rating_score', '-created_at')

    # Пагинация для новых товаров
    new_page_number = request.GET.get("new_page")
    new_paginator = Paginator(new_products, 2)
    new_page_obj = new_paginator.get_page(new_page_number)

    # Пагинация для остальных
    page_number = request.GET.get("page")
    paginator = Paginator(other_products, 4)
    page_obj = paginator.get_page(page_number)

    # Загружаем статичные товары из JSON
    static_products = {}
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'static_products.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            static_products = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Если файл не найден или поврежден, используем пустые данные
        static_products = {'new_arrivals': [], 'best_sellers': []}

    return render(request, "Market/index.html", {
        "new_page_obj": new_page_obj,
        "page_obj": page_obj,
        "static_products": static_products
    })

@csrf_exempt
def rate_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        is_like = request.POST.get('is_like') == 'true'
        user_ip = request.META.get('REMOTE_ADDR')

        # Создаем новый рейтинг (разрешаем неограниченное количество)
        ProductRating.objects.create(
            product=product,
            user_ip=user_ip,
            is_like=is_like
        )

        # Возвращаем обновленные данные
        likes_count = product.productrating_set.filter(is_like=True).count()
        dislikes_count = product.productrating_set.filter(is_like=False).count()

        return JsonResponse({
            'success': True,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'rating_score': likes_count - dislikes_count
        })

    return JsonResponse({'success': False})

@login_required
@user_passes_test(is_admin)
def update_product(request, pk):
    """Оновлення товару - доступно тільки адміністраторам"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Товар "{product.name}" успішно оновлено!')
            return redirect('Market:admin_products')
        else:
            messages.error(request, 'Помилка при оновленні товару.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'Market/update_product.html', {'form': form, 'product': product})

@login_required
@user_passes_test(is_admin)
def delete_product(request, pk):
    """Видалення товару - доступно тільки адміністраторам"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успішно видалено!')
        return redirect('Market:admin_products')
    return render(request, 'Market/delete.html', {'product': product})
def test(request):
    send_mail(
        subject='Привіт з Django + SendGrid!',
        message='Це реальне повідомлення, надіслане через SendGrid.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['artemsemenov15@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("Лист надіслано через SendGrid!")





def sendgrid_email(request):
    subject = 'Привіт з Django + SendGrid!'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = ['artemsemenov15@gmail.com']

    text_content = 'Це резервний текст для поштових клієнтів без HTML.'
    html_content = """
             <html>
                 <body style="font-family:sans-serif; background-color:#f9f9f9; padding:20px;">
                     <h2 style="color:#4CAF50;">Привіт!</h2>
                     <p>Це <strong>HTML-повідомлення</strong>, надіслане з Django через SendGrid.</p>
                     <a href="https://yourproject.com" style="display:inline-block; padding:10px 20px; background:#4CAF50; color:white; text-decoration:none; border-radius:5px;">
                         Перейти на сайт
                     </a>
                 </body>
             </html>
         """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    return HttpResponse("HTML-лист надіслано через SendGrid!")


def test_massegas(request):
    messages.success(request,"u will be killed")
    messages.error(request,"an error")
    return render(request, 'Market/messages.html', )


@csrf_exempt
def click_counter(request):
    count = int(request.COOKIES.get('clicks', 0))
    if request.method == 'POST':
        count += 1
    response = render(request, 'Market/click_counter.html', {'count': count})
    response.set_cookie('clicks', count)
    return response


@csrf_exempt
def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        # Визначаємо користувача або використовуємо None для анонімних
        user = request.user if request.user.is_authenticated else None
        
        # Створюємо або оновлюємо елемент кошика
        if user:
            cart_item, created = Cart.objects.get_or_create(
                user=user,
                product=product,
                defaults={'quantity': 1}
            )
        else:
            # Для анонімних користувачів створюємо новий запис кожен раз
            cart_item = Cart.objects.create(
                user=None,
                product=product,
                quantity=1
            )
            created = True

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        # Отримуємо товари в кошику для поточного користувача
        if user:
            cart_items = Cart.objects.filter(user=user)
        else:
            # Для анонімних користувачів показуємо порожній кошик
            cart_items = []
            
        cart_data = []
        for item in cart_items:
            cart_data.append({
                'id': item.product.id,
                'name': item.product.name,
                'price': str(item.product.price),
                'quantity': item.quantity
            })

        return JsonResponse({
            'success': True,
            'cart_items': cart_data,
            'message': f'{product.name} додано до кошика'
        })

    return JsonResponse({'success': False})

def get_cart(request):
    # Отримуємо товари в кошику для поточного користувача
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = []
        
    cart_data = []
    total_price = 0

    for item in cart_items:
        item_total = item.product.price * item.quantity
        total_price += item_total
        cart_data.append({
            'id': item.product.id,
            'name': item.product.name,
            'price': str(item.product.price),
            'quantity': item.quantity,
            'total': str(item_total)
        })

    return JsonResponse({
        'cart_items': cart_data,
        'total_price': str(total_price)
    })


@csrf_exempt
def update_cart_quantity(request, product_id):
    """Оновлення кількості товару в кошику"""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Потрібна авторизація'})
        
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            # Видаляємо товар з кошика, якщо кількість 0 або менше
            Cart.objects.filter(user=request.user, product=product).delete()
            message = f'{product.name} видалено з кошика'
        else:
            # Оновлюємо кількість
            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity = quantity
                cart_item.save()
            message = f'Кількість {product.name} оновлено'

        # Отримуємо оновлені дані кошика
        cart_items = Cart.objects.filter(user=request.user)
        cart_data = []
        total_price = 0

        for item in cart_items:
            item_total = item.product.price * item.quantity
            total_price += item_total
            cart_data.append({
                'id': item.product.id,
                'name': item.product.name,
                'price': str(item.product.price),
                'quantity': item.quantity,
                'total': str(item_total)
            })

        return JsonResponse({
            'success': True,
            'cart_items': cart_data,
            'total_price': str(total_price),
            'message': message
        })

    return JsonResponse({'success': False})


@csrf_exempt
def remove_from_cart(request, product_id):
    """Видалення товару з кошика"""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Потрібна авторизація'})
        
        product = get_object_or_404(Product, id=product_id)
        Cart.objects.filter(user=request.user, product=product).delete()
        
        # Отримуємо оновлені дані кошика
        cart_items = Cart.objects.filter(user=request.user)
        cart_data = []
        total_price = 0

        for item in cart_items:
            item_total = item.product.price * item.quantity
            total_price += item_total
            cart_data.append({
                'id': item.product.id,
                'name': item.product.name,
                'price': str(item.product.price),
                'quantity': item.quantity,
                'total': str(item_total)
            })

        return JsonResponse({
            'success': True,
            'cart_items': cart_data,
            'total_price': str(total_price),
            'message': f'{product.name} видалено з кошика'
        })

    return JsonResponse({'success': False})




@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Комплексна адмін панель - всі функції на одній сторінці"""
    # Обробка форм
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_product':
            product_form = ProductForm(request.POST)
            if product_form.is_valid():
                product = product_form.save()
                messages.success(request, f'Товар "{product.name}" успішно додано!')
                return redirect('Market:admin_dashboard')
            else:
                messages.error(request, 'Помилка при додаванні товару.')
        
        elif action == 'edit_product':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id)
            product_form = ProductForm(request.POST, instance=product)
            if product_form.is_valid():
                product_form.save()
                messages.success(request, f'Товар "{product.name}" успішно оновлено!')
                return redirect('Market:admin_dashboard')
            else:
                messages.error(request, 'Помилка при оновленні товару.')
        
        elif action == 'delete_product':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id)
            product_name = product.name
            product.delete()
            messages.success(request, f'Товар "{product_name}" успішно видалено!')
            return redirect('Market:admin_dashboard')
        
        elif action == 'add_admin':
            admin_form = AdminRegistrationForm(request.POST)
            if admin_form.is_valid():
                admin = admin_form.save(commit=False)
                admin.set_password(admin_form.cleaned_data['password'])
                admin.save()
                messages.success(request, f'Адміністратор {admin.username} успішно створений!')
                return redirect('Market:admin_dashboard')
            else:
                messages.error(request, 'Помилка при створенні адміністратора.')
    
    # Отримуємо всі товари з рейтингами
    products = Product.objects.annotate(
        annotated_likes_count=Count(Case(When(productrating__is_like=True, then=1), output_field=IntegerField())),
        annotated_dislikes_count=Count(Case(When(productrating__is_like=False, then=1), output_field=IntegerField())),
        annotated_rating_score=Count(Case(When(productrating__is_like=True, then=1), output_field=IntegerField())) -
                    Count(Case(When(productrating__is_like=False, then=1), output_field=IntegerField()))
    ).order_by('-created_at')
    
    # Пагінація
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Форми для модальних вікон
    product_form = ProductForm()
    admin_form = AdminRegistrationForm()
    
    # Статистика
    total_products = products.count()
    total_admins = CustomUser.objects.filter(is_staff=True).count()
    total_users = CustomUser.objects.count()
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    context = {
        'page_obj': page_obj,
        'total_products': total_products,
        'total_admins': total_admins,
        'total_users': total_users,
        'recent_products': recent_products,
        'product_form': product_form,
        'admin_form': admin_form,
    }
    
    return render(request, 'Market/admin_dashboard.html', context)


def admin_products(request):
    """Перенаправлення на нову адмін панель"""
    return redirect('Market:admin_dashboard')
