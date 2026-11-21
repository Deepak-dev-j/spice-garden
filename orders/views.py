from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from menu.models import FoodItem
from . import cart as cart_service
from .forms import CheckoutForm
from .models import Coupon, Order, Payment
from .services import cancel_order, place_order


def _safe_next(request, default):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return default


@require_POST
def add_to_cart(request, food_id):
    item = get_object_or_404(FoodItem, pk=food_id, is_available=True)
    cart_service.add_item(request.session, item.pk)
    messages.success(request, f"Added {item.name} to your cart.")
    return redirect(_safe_next(request, reverse("cart")))


def cart_view(request):
    return render(request, "cart.html", {"summary": cart_service.summarize(request.session)})


@require_POST
def cart_update(request):
    try:
        food_id = int(request.POST.get("food_id", ""))
    except ValueError:
        messages.error(request, "That item could not be updated.")
        return redirect("cart")

    action = request.POST.get("action")
    qty = cart_service.get_qty(request.session, food_id)
    if action == "increase":
        cart_service.set_qty(request.session, food_id, qty + 1)
    elif action == "decrease":
        cart_service.set_qty(request.session, food_id, qty - 1)
    elif action == "remove":
        cart_service.set_qty(request.session, food_id, 0)
        messages.info(request, "Item removed from your cart.")
    return redirect("cart")


@require_POST
def coupon_apply(request):
    code = request.POST.get("code", "").strip().upper()
    coupon = Coupon.objects.filter(code=code).first()
    if not coupon:
        messages.error(request, "That coupon code is not valid.")
        return redirect("cart")
    subtotal = cart_service.summarize(request.session)["subtotal"]
    error = coupon.error_for(subtotal)
    if error:
        messages.error(request, error)
        return redirect("cart")
    cart_service.set_coupon(request.session, coupon.code)
    messages.success(request, f"Coupon {coupon.code} applied!")
    return redirect("cart")


@require_POST
def coupon_remove(request):
    cart_service.clear_coupon(request.session)
    messages.info(request, "Coupon removed.")
    return redirect("cart")


@login_required
def checkout(request):
    summary = cart_service.summarize(request.session)
    if not summary["lines"]:
        messages.info(request, "Your cart is empty. Add something tasty first!")
        return redirect("menu")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = place_order(request.user, summary, **form.cleaned_data)
            cart_service.clear(request.session)
            return redirect("order_success", pk=order.pk)
    else:
        default = request.user.addresses.filter(is_default=True).first() or request.user.addresses.first()
        form = CheckoutForm(initial={
            "name": request.user.get_full_name() or request.user.username,
            "phone": default.phone if default else "",
            "address": default.as_text if default else "",
        })
    return render(request, "checkout.html", {"form": form, "summary": summary})


@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "order_success.html", {"order": order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items", "refunds"), pk=pk, user=request.user)
    flow = [choice for choice in Order.Status.choices if choice[0] != Order.Status.CANCELLED]
    flow_values = [value for value, _ in flow]
    current = flow_values.index(order.status) if order.status in flow_values else -1
    timeline = [
        {"label": label, "done": current >= index}
        for index, (value, label) in enumerate(flow)
        if value != Order.Status.READY or order.status == Order.Status.READY
    ]
    payment = Payment.objects.filter(order=order).first()
    return render(request, "order_detail.html", {"order": order, "timeline": timeline, "payment": payment})


@login_required
@require_POST
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    try:
        refund_created = cancel_order(order)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        extra = " A refund request has been created." if refund_created else ""
        messages.success(request, f"Order #{order.pk} has been cancelled.{extra}")
    return redirect("order_detail", pk=order.pk)
