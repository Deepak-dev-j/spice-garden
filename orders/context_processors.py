from django.conf import settings


def cart(request):
    cart_data = request.session.get("cart", {})
    return {"cart_count": sum(cart_data.values())}


def site(request):
    return {
        "site": {
            "name": settings.RESTAURANT_NAME,
            "hours": settings.RESTAURANT_HOURS,
            "address": settings.RESTAURANT_ADDRESS,
            "email": settings.SUPPORT_EMAIL,
            "phone": settings.SUPPORT_PHONE,
        }
    }
