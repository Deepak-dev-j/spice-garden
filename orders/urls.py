from django.urls import path

from . import views

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:food_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/coupon/apply/", views.coupon_apply, name="cart_coupon_apply"),
    path("cart/coupon/remove/", views.coupon_remove, name="cart_coupon_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/success/", views.order_success, name="order_success"),
    path("orders/<int:pk>/cancel/", views.order_cancel, name="order_cancel"),
]
