from django.contrib import admin

from .models import Coupon, Order, OrderItem, Payment, Refund


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("name", "price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ("reference", "amount", "method")

    def has_add_permission(self, request, obj=None):
        return False


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "percent_off", "flat_off", "min_order", "active", "valid_until")
    list_editable = ("active",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "user", "status", "payment_status", "total", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "payment_status", "payment_method")
    search_fields = ("id", "customer_name", "phone", "user__username")
    readonly_fields = ("subtotal", "discount", "tax", "delivery_fee", "total", "created_at", "updated_at")
    inlines = [OrderItemInline, PaymentInline, RefundInline]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == Refund.Status.COMPLETED:
            Order.objects.filter(pk=obj.order_id).update(payment_status=Order.PaymentStatus.REFUNDED)
            Payment.objects.filter(order_id=obj.order_id).update(status=Order.PaymentStatus.REFUNDED)
