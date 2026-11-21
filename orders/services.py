"""Business logic for placing and cancelling orders. All money math is server-side."""
import uuid

from django.db import transaction

from .models import Order, OrderItem, Payment, Refund


def place_order(user, summary, *, name, phone, address, payment_method, note=""):
    online = payment_method == Order.PaymentMethod.ONLINE
    payment_status = Order.PaymentStatus.PAID if online else Order.PaymentStatus.PENDING

    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            coupon=summary["coupon"],
            customer_name=name,
            phone=phone,
            delivery_address=address,
            special_note=note,
            payment_method=payment_method,
            payment_status=payment_status,
            subtotal=summary["subtotal"],
            discount=summary["discount"],
            tax=summary["tax"],
            delivery_fee=summary["delivery_fee"],
            total=summary["total"],
        )
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                food_item=line["item"],
                name=line["item"].name,
                price=line["item"].price,
                quantity=line["qty"],
            )
            for line in summary["lines"]
        ])
        prefix = "DEMO" if online else "COD"
        Payment.objects.create(
            order=order,
            method=payment_method,
            amount=order.total,
            status=payment_status,
            reference=f"{prefix}-{uuid.uuid4().hex[:10].upper()}",
        )
    return order


def cancel_order(order):
    """Cancels an order. Returns True if a refund request was created."""
    if not order.is_cancellable:
        raise ValueError(
            f"Order #{order.pk} is already {order.get_status_display().lower()} and can no longer be cancelled."
        )
    with transaction.atomic():
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        if order.payment_status == Order.PaymentStatus.PAID:
            Refund.objects.create(
                order=order,
                amount=order.total,
                reason="Cancelled by customer",
                status=Refund.Status.REQUESTED,
            )
            return True
    return False
