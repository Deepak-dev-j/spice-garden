"""Session-based shopping cart. The cart lives in the session, prices always come from SQLite."""
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

from menu.models import FoodItem
from .models import Coupon

CART_KEY = "cart"
COUPON_KEY = "coupon_code"
MAX_QTY = 20
ZERO = Decimal("0.00")


def _raw(session):
    return dict(session.get(CART_KEY, {}))


def _save(session, cart):
    session[CART_KEY] = cart
    session.modified = True


def get_qty(session, food_id):
    return _raw(session).get(str(food_id), 0)


def set_qty(session, food_id, qty):
    cart = _raw(session)
    if qty <= 0:
        cart.pop(str(food_id), None)
    else:
        cart[str(food_id)] = min(qty, MAX_QTY)
    _save(session, cart)


def add_item(session, food_id, qty=1):
    set_qty(session, food_id, get_qty(session, food_id) + qty)


def clear(session):
    session.pop(CART_KEY, None)
    session.pop(COUPON_KEY, None)
    session.modified = True


def set_coupon(session, code):
    session[COUPON_KEY] = code
    session.modified = True


def clear_coupon(session):
    session.pop(COUPON_KEY, None)
    session.modified = True


def get_lines(session):
    cart = _raw(session)
    items = FoodItem.objects.in_bulk([int(k) for k in cart]) if cart else {}
    lines = []
    for key, qty in cart.items():
        item = items.get(int(key))
        if item and item.is_available:
            lines.append({"item": item, "qty": qty, "subtotal": item.price * qty})
    return lines


def summarize(session):
    lines = get_lines(session)
    subtotal = sum((line["subtotal"] for line in lines), ZERO)

    coupon, discount = None, ZERO
    code = session.get(COUPON_KEY)
    if code:
        candidate = Coupon.objects.filter(code=code).first()
        if candidate and candidate.error_for(subtotal) is None:
            coupon = candidate
            discount = candidate.discount_for(subtotal)

    taxable = subtotal - discount
    tax = (taxable * settings.TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    delivery = ZERO if (not lines or subtotal >= settings.FREE_DELIVERY_ABOVE) else settings.DELIVERY_FEE
    total = taxable + tax + delivery

    return {
        "lines": lines,
        "item_count": sum(line["qty"] for line in lines),
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "delivery_fee": delivery,
        "total": total,
        "coupon": coupon,
    }
