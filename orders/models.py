from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from menu.models import FoodItem


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=120, blank=True)
    percent_off = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(90)])
    flat_off = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"),
                                   validators=[MinValueValidator(Decimal("0"))])
    min_order = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    valid_until = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def error_for(self, subtotal):
        """Returns a customer-friendly reason the coupon cannot be used, or None if valid."""
        if not self.active:
            return "This coupon is not active."
        if self.valid_until and self.valid_until < timezone.localdate():
            return "This coupon has expired."
        if subtotal < self.min_order:
            return f"Add items worth ₹{self.min_order} or more to use this coupon."
        return None

    def discount_for(self, subtotal):
        amount = subtotal * Decimal(self.percent_off) / Decimal(100) + self.flat_off
        return min(amount, subtotal).quantize(Decimal("0.01"))


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Order Placed"
        CONFIRMED = "confirmed", "Order Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready for Pickup"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on Delivery"
        ONLINE = "online", "Online Payment (demo)"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLACED, db_index=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15)
    delivery_address = models.TextField()
    special_note = models.CharField(max_length=200, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"Order #{self.pk}"

    @property
    def is_cancellable(self):
        return self.status in (self.Status.PLACED, self.Status.CONFIRMED)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    food_item = models.ForeignKey(FoodItem, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.name}"


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=10, choices=Order.PaymentMethod.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Order.PaymentStatus.choices)
    reference = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order_id}"


class Refund(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refunds")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund for Order #{self.order_id}"
