
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from .forms import ProductForm, CommentForm
from .models import Product, Cart
from django.urls import reverse

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


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('Market:view_cart')



def view_cart(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            item.total_price = item.product.price * item.quantity
        total_sum = sum(item.total_price for item in cart_items)
    else:
        cart_data = request.session.get('cart', {})
        cart_items = []
        total_sum = 0
        for product_id, quantity in cart_data.items():
            try:
                product = Product.objects.get(pk=product_id)
                total_price = product.price * quantity
                total_sum += total_price
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': total_price
                })
            except Product.DoesNotExist:
                continue

    return render(request, 'Market/cart.html', {
        'cart_items': cart_items,
        'total_sum': total_sum
    })


def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = Cart.objects.filter(user=request.user, product=product).first()
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    else:
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            if cart[str(product_id)] > 1:
                cart[str(product_id)] -= 1
            else:
                del cart[str(product_id)]
            request.session['cart'] = cart

    return redirect('Market:view_cart')


from django.shortcuts import redirect, get_object_or_404
from .models import Product, Cart

def add_one_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart = request.session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        request.session['cart'] = cart

    return redirect('Market:view_cart')

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

