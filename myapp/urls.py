from django.urls import path
from django.shortcuts import render
from . import views
from .views import *

urlpatterns = [
    path('register/', RegisterForm.as_view(), name='register'),
    path('', LoginForm.as_view(), name='login'),
    path('home/', HomePage.as_view(), name='home'),
    path('product/<int:id>/', DetailPage.as_view(), name='detail_page'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('product_cart/<int:id>/', CartView.as_view(), name='add_to_cart'),
    path('cart/', CartPageView.as_view(), name='cart'),
    path("remove_cart/<int:id>/", Remove_cart.as_view(), name="remove_cart"),
    path('add_item/', AddItem.as_view(), name='view_item'),

    path('checkout/', lambda request: render(request, 'bag.html'), name='checkout'),
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('success/', payment_success, name="success"),
    path('cancel/', payment_cancel, name="cancel"),
    path("webhook/", stripe_webhook, name="stripe-webhook"),

    path('my_orders/', MyOrdersView.as_view(), name='my_orders'),
    path('wishlist/remove/<int:item_id>/', RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),
    path('wishlist/move_to_cart/<int:item_id>/', MoveToCartView.as_view(), name='move_to_cart'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('product_wishlist/<int:product_id>/', AddToWishlistView.as_view(), name='add_to_wishlist'),


    path('verify/', verify_email.as_view(), name='verify_email'),

    path('profile/', views.ProfileView.as_view(), name='my_profile'),
    path('my_profile/', views.ProfileView.as_view(), name='my_profile'),
    path('verify_phone/', VerifyPhoneView.as_view(), name='verify_phone'),
    path('send_otp/', SendOTPView.as_view(), name='send_otp'),
    path('search/', SearchProductsView.as_view(), name='search_products'),

    path('men/', MenView.as_view(), name='men'),
    path('men_shirts/', MenShirtsView.as_view(), name='men_shirts'),
    path('men_polos/', MenPoloView.as_view(), name='men_polos'),
    path('men_bottomwear/', MenBottomwearView.as_view(), name='men_bottomwear'),

    path('women/', WomenView.as_view(), name='women'),
    path('women_topwear/', WomenTopwearView.as_view(), name='women_topwear'),
    path('women_bottomwear/', WomenBottomwearView.as_view(), name='women_bottomwear'),

    path('accessories/', AccessoriesView.as_view(), name='accessories'),
    path('accessories_belts/', AccessoriesBeltsView.as_view(), name='accessories_belts'),
    path('accessories_socks/', AccessoriesSocksView.as_view(), name='accessories_socks'),
]
