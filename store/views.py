from django.shortcuts import render, redirect
from django.views.generic import ListView, View
from .models import Product, Order, OrderItem, Address, Payment
from django.shortcuts import get_object_or_404
from django.contrib import messages
from datetime import datetime
from booklover import settings
from django.db.models import Q


from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .form import CreateUserForm
import stripe


# unauthenticated user
def unauthenticated_user(func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return func(request, *args, **kwargs)
    return wrapper


@unauthenticated_user
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@unauthenticated_user
def signup(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=username, password=raw_password)
            # login(request, user)
            messages.success(request, 'Account created successfully')
            return redirect('home')
    else:
        form = CreateUserForm()
    return render(request, 'signup.html', {'form': form})


class Store(ListView):
    model = Product
    template_name = 'store.html'


def Search(request):
    search = request.GET.get('search')
    if search is not None:
        qs = Product.objects.filter(Q(name__contains=search) | Q(description__contains=search) | Q(category__name__contains=search)).distinct()
        context = {
            'books': qs
        }
    else:
        return redirect('home')
    return render(request, 'search.html', context)


def book(request, slug):
    qs = get_object_or_404(Product, slug=slug)
    context = {'book': qs}
    return render(request, 'book.html', context)


@login_required(login_url='login')
def add_to_cart(request, slug):
    order, created = Order.objects.get_or_create(user=request.user, ordered=False)
    order_qs = order
    order_item = order_qs.orderitem_set.filter(product__slug=slug)

    if order_item.exists():
        order_item = order_item.first()
        order_item.quantity += 1
        order_item.save()
    else:
        product = Product.objects.get(slug=slug)
        order_item_create = OrderItem.objects.create(order=order_qs, product=product)
        order_item_create.save()

    if request.GET.get('cart_page') == 'True':
        return redirect('cart')
    return redirect('home')


@login_required(login_url='login')
def remove_to_cart(request, slug):
    order_qs = Order.objects.filter(user=request.user, ordered=False).first()
    order_item = order_qs.orderitem_set.filter(product__slug=slug)
    if order_item.exists():
        order_item = order_item.first()
        if order_item.quantity < 2:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save()
    return redirect('cart')


@login_required(login_url='login')
def cartView(request):
    order, created = Order.objects.get_or_create(user=request.user, ordered=False)
    order_item = order.orderitem_set.all()
    context = {
        'order_item': order_item,
        'total': order.get_total()
    }
    return render(request, 'cart.html', context)


@login_required(login_url='login')
def checkoutView(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        full_address = request.POST.get('full_address')
        phone = request.POST.get('phone')
        default = request.POST.get('default')
        payment_method = request.POST.get('payment_method')
        default_shipping = request.POST.get('default_shipping')

        # Default shipping check
        if default_shipping is None:
            if default is None:
                default_address = False
            else:
                try:
                    default_qs = Address.objects.filter(user=request.user, default=True).first()
                    default_qs.default = False
                    default_qs.save()
                    default_address = True
                finally:
                    default_address = True

            if full_address is not '' and phone is not '':
                address_create = Address.objects.create(user=request.user, name=name, full_address=full_address, phone=phone,
                                                        default=default_address)
                address_create.save()
            else:
                return redirect('checkout')
        else:
            address_create = Address.objects.filter(user=request.user, default=True).first()

        if payment_method == 'COD':
            order_qs = Order.objects.filter(user=request.user, ordered=False).first()
            order_qs.shipping_address = address_create
            order_qs.payment_method = 'COD'
            order_qs.ordered_date = datetime.now()
            order_qs.ordered = True
            order_qs.save()
            messages.success(request, 'Order placed successfully.')
            return redirect('home')
        elif payment_method == 'STRIP':
            order_qs = Order.objects.filter(user=request.user, ordered=False).first()
            order_qs.shipping_address = address_create
            order_qs.payment_method = 'STRIP'
            order_qs.ordered_date = datetime.now()
            order_qs.save()
            return redirect('payment')
        else:
            return redirect('checkout')

    default_address_get = Address.objects.filter(user=request.user, default=True).first()

    if default_address_get is None:
        default_address_get = 'False'

    context = {
        'default_address': default_address_get
    }
    return render(request, 'checkout.html', context)


@login_required(login_url='login')
def payment(request):
    order = Order.objects.filter(user=request.user, ordered=False, payment_method='STRIP')
    order_qs = order.first()
    print(order_qs.get_total())
    if not order.exists():
        return redirect('checkout')

    if request.method == 'POST':
        try:
            stripe.api_key = settings.STRIP_SECRETE_KEY
            token = request.POST.get('stripeToken')

            order_qs = order.first()

            print(token)

            charge = stripe.Charge.create(
                      amount=order_qs.get_total() * 100,
                      currency="usd",
                      source=token,
                      description="My First Test Charge (created for API docs)",
                    )
            print(charge)
            charge_payment = Payment.objects.create(
                strip_token_id=charge.id,
                user=request.user,
                amount=order_qs.get_total()
            )
            charge_payment.save()

            order_qs.ordered = True
            order_qs.payment = charge_payment
            order_qs.save()
            messages.success(request, 'Order placed successfully.')
            return redirect('home')

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(request, f"{err.get('message')}")
            return redirect("payment")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(request, "Rate limit error")
            return redirect("payment")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(request, "Invalid parameters")
            return redirect("payment")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(request, "Not authenticated")
            return redirect("payment")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(request, "Network error")
            return redirect("payment")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(request, "Something went wrong. You were not charged. Please try again.")
            return redirect("payment")

        except Exception as e:
            # send an email to ourselves
            messages.warning(request, "A serious error occurred. We have been notifed.")
            return redirect("payment")

    context = {
        'strip_public_key': settings.STRIP_PUBLIC_KEY
    }

    return render(request, 'payment.html', context)


@login_required(login_url='login')
def Orders(request):
    orders = Order.objects.order_by('-ordered_date').filter(user=request.user, ordered=True)
    context = {
        'orders': orders
    }
    return render(request, 'orders.html', context)


