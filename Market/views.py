from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from .forms import ProductForm, CommentForm
from .models import Product, Cart, Purchase, BonusProduct
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

    for item in cart_items:
        if item.is_bonus_purchase:  # Обробляємо бонусні товари
            try:
                bonus_price = item.product.bonus_info.bonus_price  # Отримуємо бонусну ціну
            except:
                bonus_price = item.product.price  # Якщо немає бонусної ціни, використовуємо звичайну
            item.total_price = bonus_price * item.quantity  # Розраховуємо загальну вартість
            item.bonus_price = bonus_price  # Зберігаємо бонусну ціну для відображення
            item.is_bonus = True  # Позначаємо як бонусний товар
        else:
            item.total_price = item.product.price * item.quantity  # Розраховуємо звичайну вартість
            item.is_bonus = False  # Позначаємо як звичайний товар

    regular_items = [item for item in cart_items if not item.is_bonus_purchase]  # Звичайні товари
    bonus_items = [item for item in cart_items if item.is_bonus_purchase]  # Бонусні товари
    
    regular_total = sum(item.total_price for item in regular_items)  # Загальна сума звичайних товарів
    bonus_total = sum(item.total_price for item in bonus_items)  # Загальна сума бонусних товарів
    
    from decimal import Decimal
    bonus_points = regular_total * Decimal('0.25') if regular_total else 0  # Розраховуємо бонуси що будуть нараховані

    return render(request, 'Market/cart.html', {
        'cart_items': cart_items,
        'regular_items': regular_items,
        'bonus_items': bonus_items,
        'regular_total': regular_total,
        'bonus_total': bonus_total,
        'total_sum': regular_total,
        'bonus_points': bonus_points,
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
    
    regular_items = cart_items.filter(is_bonus_purchase=False)  # Звичайні товари для покупки
    bonus_items = cart_items.filter(is_bonus_purchase=True)  # Бонусні товари для покупки
    
    total_bonus_cost = Decimal('0.00')  # Загальна вартість бонусних товарів
    total_earned_bonus = Decimal('0.00')  # Загальна кількість нарахованих бонусів

    for item in bonus_items:  # Обробляємо кожен бонусний товар
        try:
            bonus_price = item.product.bonus_info.bonus_price  # Отримуємо бонусну ціну
        except:
            bonus_price = item.product.price  # Використовуємо звичайну ціну якщо немає бонусної

        item_cost = bonus_price * item.quantity  # Розраховуємо вартість товару
        total_bonus_cost += item_cost  # Додаємо до загальної суми

        if request.user.bonus_points < item_cost:  # Перевіряємо достатність балів
            messages.error(request, f'Недостатньо бонусних балів для покупки {item.product.name}')
            return redirect('user_cart')

    if total_bonus_cost > 0:  # Якщо є бонусні покупки
        request.user.bonus_points -= total_bonus_cost  # Списуємо бонусні бали з рахунку

    for item in regular_items:  # Обробляємо звичайні товари
        bonus_earned = (item.product.price * item.quantity) * Decimal('0.01')  # Нараховуємо 1% бонусів від покупки
        total_earned_bonus += bonus_earned  # Додаємо до загальної суми нарахованих бонусів

    request.user.bonus_points += total_earned_bonus  # Додаємо нараховані бонуси до рахунку

    for item in cart_items:
        if item.is_bonus_purchase:  # Створюємо запис бонусної покупки
            try:
                bonus_price = item.product.bonus_info.bonus_price  # Отримуємо бонусну ціну
            except:
                bonus_price = item.product.price  # Використовуємо звичайну ціну
            Purchase.objects.create(  # Створюємо запис покупки
                user=request.user,
                product=item.product,
                quantity=item.quantity,
                total_price=bonus_price * item.quantity,  # Загальна вартість
                paid_with_bonus=bonus_price * item.quantity,  # Сума сплачена бонусами
                is_bonus_purchase=True  # Позначаємо як бонусну покупку
            )
        else:  # Створюємо запис звичайної покупки
            bonus_earned = (item.product.price * item.quantity) * Decimal('0.01')  # Розраховуємо нараховані бонуси
            Purchase.objects.create(  # Створюємо запис покупки
                user=request.user,
                product=item.product,
                quantity=item.quantity,
                total_price=item.product.price * item.quantity,  # Загальна вартість
                bonus_points_earned=bonus_earned,  # Нараховані бонуси
                is_bonus_purchase=False  # Позначаємо як звичайну покупку
            )
    
    request.user.save()  # Зберігаємо зміни в балансі користувача
    cart_items.delete()  # Очищуємо кошик після покупки
    
    if total_bonus_cost > 0 and total_earned_bonus > 0:
        messages.success(request, f'Покупка успішна! Витрачено {total_bonus_cost} бонусних балів і нараховано {total_earned_bonus} нових балів')
    elif total_bonus_cost > 0:
        messages.success(request, f'Покупка успішна! Витрачено {total_bonus_cost} бонусних балів')
    elif total_earned_bonus > 0:
        messages.success(request, f'Покупка успішна! Нараховано {total_earned_bonus} бонусних балів')
    else:
        messages.success(request, 'Покупка успішна!')

    return redirect('index')

@login_required 
def bonus_shop(request):
    products = Product.objects.all()

    for product in products:
        if hasattr(product, 'bonus_info'):
            product.bonus_price = product.bonus_info.bonus_price
            product.is_bonus_available = product.bonus_info.is_available
        else:
            product.bonus_price = product.price
            product.is_bonus_available = True

    return render(request, 'Market/bonus_shop.html', {
        'products': products,
        'user_bonus_points': request.user.bonus_points,  # Поточний баланс бонусних балів користувача
    })

@login_required
def add_bonus_to_cart(request, product_id):
    """Додавання товару в кошик для бонусної покупки"""
    product = get_object_or_404(Product, id=product_id)  # Отримуємо товар або помилку 404
    
    if hasattr(product, 'bonus_info'):  # Перевіряємо наявність бонусної інформації
        bonus_price = product.bonus_info.bonus_price  # Використовуємо бонусну ціну
    else:
        bonus_price = product.price  # Використовуємо звичайну ціну

    if request.user.bonus_points < bonus_price:  # Перевіряємо достатність балів
        messages.error(request, f'Недостатньо бонусних балів. Потрібно: {bonus_price}, у вас: {request.user.bonus_points}')
        return redirect('Market:bonus_shop')  # Повертаємо до бонусного магазину
    
    cart_item, created = Cart.objects.get_or_create(  # Знаходимо або створюємо товар в кошику
        user=request.user,
        product=product,
        is_bonus_purchase=True,  # Позначаємо як бонусну покупку
        defaults={'quantity': 1}  # Початкова кількість для нового товару
    )
    
    if created:
        messages.success(request, f'"{product.name}" додано в кошик! Ціна: {bonus_price} балів')
    else:
        new_total_cost = bonus_price * (cart_item.quantity + 1)
        if request.user.bonus_points < new_total_cost:
            messages.error(request, f'Недостатньо балів для збільшення кількості. Потрібно: {new_total_cost}')
            return redirect('Market:bonus_shop')

        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Кількість "{product.name}" збільшено! Ціна: {bonus_price} балів за шт.')
    
    return redirect('Market:bonus_shop')

@login_required
def remove_bonus_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # Отримуємо товар або помилку 404
    
    try:
        cart_item = Cart.objects.get(  # Знаходимо товар в кошику
            user=request.user,  # Для поточного користувача
            product=product,  # Конкретний товар
            is_bonus_purchase=True  # Тільки бонусні товари
        )

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f'Кількість "{product.name}" зменшено в кошику!')  # Повідомляємо про успіх
        else:
            cart_item.delete()
            messages.success(request, f'"{product.name}" видалено з кошика!')
    except Cart.DoesNotExist:
        messages.error(request, 'Товар не знайдено в кошику!')
    
    return redirect('Market:view_cart')



