from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

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

    # бонусні бали
    user_bonus_points = 0
    if request.user.is_authenticated:
        user_bonus_points = request.user.bonus_points

    return render(request, 'Market/menu.html', {
        'sections': sections,
        'products': products,
        'user_bonus_points': user_bonus_points,
    })


def index(request):
    return render(request, 'Market/index.html')
def add_product(request):
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

        return redirect('Market:menu')
    return render(request, 'Market/product.html')

def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('Market:menu')
    return render(request, 'Market/confirm_delete.html', {'product': product})


def edit_product(request, pk):
    product = Product.objects.get(id=pk)

    if request.method == "GET":
        form = ProductForm(instance=product)
        return render(request, "Market/edit.html", {'form': form})

    form = ProductForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
        form.save()
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

    return redirect('index')



@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = sum(item.product.price * item.quantity for item in cart_items)

    bonus_points_to_earn = total * Decimal('0.10')
    
    return render(request, 'Market/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'bonus_points_to_earn': bonus_points_to_earn,
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



from django.shortcuts import redirect, get_object_or_404
from .models import Product, Cart

@login_required
def add_one_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

    cart_item.quantity += 1
    cart_item.save()

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
        messages.error(request, 'Ваш кошик порожній')
        return redirect('user_cart')
    
    total_cost = sum(item.product.price * item.quantity for item in cart_items)
    
    use_bonus = request.POST.get('use_bonus') == 'on'
    bonus_used = Decimal('0')

    if use_bonus and request.user.bonus_points > 0:
        bonus_used = min(request.user.bonus_points, total_cost)
        total_cost -= bonus_used
        request.user.bonus_points -= bonus_used

    bonus_earned = total_cost * Decimal('0.10')
    request.user.bonus_points += bonus_earned
    request.user.save()

    for item in cart_items:
        Purchase.objects.create(
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            total_price=item.product.price * item.quantity,
            bonus_points_earned=bonus_earned / len(cart_items)
        )
    
    cart_items.delete()
    
    message = f'Покупка успішна!'
    if bonus_used > 0:
        message += f' Використано {bonus_used} балів.'
    if bonus_earned > 0:
        message += f' Нараховано {bonus_earned} балів.'

    messages.success(request, message)
    return redirect('index')

@login_required
def add_to_cart_with_bonus(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.bonus_points < product.price:
        messages.error(request, f'Недостатньо балів! Ціна: {product.price} бонусних балів')
        return redirect('Market:menu')

    request.user.bonus_points -= product.price
    request.user.save()

    Purchase.objects.create(
        user=request.user,
        product=product,
        quantity=1,
        total_price=product.price,
        bonus_points_earned=0
    )

    messages.success(request, f'"{product.name}" придбано за {product.price} балів!')
    return redirect('Market:menu')

@login_required
def bonus_products(request):
    products = Product.objects.all()
    sections = ['Піца', 'Суші', 'Салати', 'Напої', 'Десерти']

    return render(request, 'Market/bonus_products.html', {
        'sections': sections,
        'products': products,
        'user_bonus_points': request.user.bonus_points,
    })