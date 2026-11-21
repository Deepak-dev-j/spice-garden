from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import render

from orders.models import Coupon
from .models import Category, FoodItem

SORTS = {
    "price_asc": ("price",),
    "price_desc": ("-price",),
    "rating": ("-rating",),
    "popular": ("-is_popular", "-rating"),
}


def home(request):
    context = {
        "categories": Category.objects.all(),
        "popular_items": FoodItem.objects.filter(is_available=True, is_popular=True)[:8],
        "offers": Coupon.objects.filter(active=True)[:3],
    }
    return render(request, "home.html", context)


def menu_list(request):
    items = FoodItem.objects.select_related("category")
    q = request.GET.get("q", "").strip()[:100]
    category = request.GET.get("category", "")
    veg = request.GET.get("veg", "")
    max_price = request.GET.get("max_price", "")
    sort = request.GET.get("sort", "")

    if q:
        items = items.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(ingredients__icontains=q))
    if category:
        items = items.filter(category__slug=category)
    if veg == "veg":
        items = items.filter(is_veg=True)
    elif veg == "nonveg":
        items = items.filter(is_veg=False)
    if max_price:
        try:
            value = Decimal(max_price)
            if value.is_finite() and value >= 0:
                items = items.filter(price__lte=value)
        except (InvalidOperation, ValueError):
            pass
    if sort in SORTS:
        items = items.order_by(*SORTS[sort])

    return render(request, "menu.html", {"items": items, "categories": Category.objects.all()})
