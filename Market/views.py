from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse

from .forms import ProductForm, CommentForm
from .models import Product, Cart, Purchase
from django.urls import reverse
from decimal import Decimal
from django.contrib import messages

def index(request):
    return render(request, "Market/index.html")



def about(request):
    return render(request, "Market/about.html")

def team(request):
    return render(request, "Market/team.html")

def menu(request):
    return render(request, "Market/menu.html")


def is_admin(user):
    return user.is_superuser

def shop(request):
    products = Product.objects.all()
    sections = ['Піца', 'Суші', 'Салати', 'Напої', 'Десерти']

    return render(request, 'Market/menu.html', {
        'sections': sections,
        'products': products,
    })



@login_required
def add_product(request):
    if not request.user.is_authenticated:
        return redirect('Market:login')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        section = request.POST.get('section')  # <-- додано

        product = Product(
            name=name,
            price=price,
            description=description,
            image=image,
            section=section  # <-- додано
        )
        product.save()

        # Проверяем, откуда пришел пользователь
        referer = request.META.get('HTTP_REFERER', '')
        if 'admin' in referer:
            return redirect('Market:admin_dashboard')
        return redirect('Market:menu')
    return render(request, 'Market/product.html')

@login_required
def delete_product(request, pk):
    if not request.user.is_authenticated:
        return redirect('Market:login')
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        # Проверяем, является ли это AJAX запросом
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                product.delete()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': str(e)
                })
        
        # Обычная обработка для не-AJAX запросов
        product.delete()
        # Проверяем, откуда пришел пользователь
        referer = request.META.get('HTTP_REFERER', '')
        if 'admin' in referer:
            return redirect('Market:admin_dashboard')
        return redirect('Market:menu')
        
    return render(request, 'Market/confirm_delete.html', {'product': product})


@login_required
def edit_product(request, pk):
    if not request.user.is_authenticated:
        return redirect('Market:login')
    
    product = Product.objects.get(id=pk)

    if request.method == "GET":
        form = ProductForm(instance=product)
        return render(request, "Market/edit.html", {'form': form})

    # Проверяем, является ли это AJAX запросом
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            form = ProductForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Помилка валідації форми'
                })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    # Обычная обработка для не-AJAX запросов
    form = ProductForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
        form.save()
        # Проверяем, откуда пришел пользователь
        referer = request.META.get('HTTP_REFERER', '')
        if 'admin' in referer:
            return redirect('Market:admin_dashboard')
        return redirect('Market:menu')

    return render(request, "Market/edit.html", {'form': form})


@login_required
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('Market:menu')



@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = sum(item.product.price * item.quantity for item in cart_items)

    return render(request, 'Market/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'user_bonus_points': request.user.bonus_points
    })


@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item = Cart.objects.filter(user=request.user, product=product).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('user_cart')






def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    comments = product.comments.order_by('-created_at')
    form = CommentForm()
    captcha_error = False

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            comment.save()
            request.session['comment_success'] = True
            return redirect(f"{reverse('Market:product_detail', args=[product.id])}#comment-form")
        else:
            if 'captcha' in form.errors:
                captcha_error = True

    comment_success = request.session.pop('comment_success', False)

    return render(request, 'Market/product_detail.html', {
        'product': product,
        'comments': comments,
        'form': form,
        'comment_success': comment_success,
        'captcha_error': captcha_error,
    })



@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items:
        messages.error(request, 'Кошик порожній')
        return redirect('user_cart')

    total = sum(item.product.price * item.quantity for item in cart_items)
    payment_mode = request.POST.get('payment_mode', 'money')
    
    if payment_mode == 'bonus':
        if request.user.bonus_points >= total:
            request.user.bonus_points -= total
            request.user.save()
        else:
            return redirect('user_cart')
    else:
        bonus_earned = total * Decimal('0.10')
        request.user.bonus_points += bonus_earned
        request.user.save()

    for item in cart_items:
        Purchase.objects.create(
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            total_price=item.product.price * item.quantity,
        )
    
    cart_items.delete()
    return redirect('index')


@login_required
def admin_dashboard(request):
    """Кастомная админ-панель с ограниченным доступом"""
    if not request.user.is_authenticated:
        messages.error(request, 'Доступ заборонено! Необхідно увійти в систему.')
        return redirect('Market:login')
    
    # Базовая статистика для админ-панели
    total_products = Product.objects.count()
    total_purchases = Purchase.objects.count()
    
    context = {
        'total_products': total_products,
        'total_purchases': total_purchases,
        'products': Product.objects.all()
    }
    
    return render(request, 'Market/admin_dashboard.html', context)
