from django.shortcuts import render
from django.http import JsonResponse
import json



def index(request):
    return render(request, "Market/index.html")



def about(request):
    return render(request, "Market/about.html")

def team(request):
    return render(request, "Market/team.html")

def menu(request):
    return render(request, "Market/menu.html")


def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product_name = request.POST.get('product_name')
        product_price = float(request.POST.get('product_price'))

        cart = request.session.get('cart', {})

        if product_id in cart:
            cart[product_id]['quantity'] += 1
        else:
            cart[product_id] = {
                'name': product_name,
                'price': product_price,
                'quantity': 1
            }

        request.session['cart'] = cart
        return JsonResponse({'success': True, 'cart': cart})


def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        quantity = item['quantity']
        price = item['price']
        # Важливо: використовуємо ключі 'name' та 'price' безпосередньо з item
        item_name = item['name']
        item_total = quantity * price
        total_price += item_total

        cart_items.append({
            'name': item_name,
            'price': price,
            'quantity': quantity,
            'total': item_total
        })

    return render(request, 'Market/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

#f[f[f[[