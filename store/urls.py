from django.urls import path
from . import views

urlpatterns = [
    path('', views.Store.as_view(), name='home'),
    path('book/<slug>', views.book, name='product'),
    path('cart', views.cartView, name='cart'),
    path('add_to_card/<slug>', views.add_to_cart, name='add_to_cart'),
    path('remove_to_cart/<slug>', views.remove_to_cart, name='remove_to_cart'),
    path('checkout', views.checkoutView, name='checkout'),
    path('payment/', views.payment, name='payment'),
    path('orders', views.Orders, name='orders'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.Search, name='search'),
    # path('create-payment-intent', view.create_payment, name='create-payment-intent')
]
