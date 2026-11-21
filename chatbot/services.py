"""Chatbot brain. Every order answer is checked against the logged-in customer's own records in SQLite."""
import logging
import re

from django.conf import settings

from menu.models import Category, FoodItem
from orders.models import Coupon, Order, Payment, Refund
from orders.services import cancel_order

from . import ai, nlp, safety
from .models import SupportTicket

logger = logging.getLogger(__name__)

PENDING_KEY = "chat_pending"
FEEDBACK_INTENTS = {
    "track_order", "delayed_order", "not_received", "missing_item", "wrong_item",
    "food_quality", "refund_status", "payment_issue",
}
ORDER_ID_RE = re.compile(
    r"#\s*(\d{1,8})|\b(?:order|id|no|number)\s*(?:id|no\.?|number)?\s*:?\s*#?\s*(\d{1,8})\b|\b(\d{1,8})\b"
)

CLARIFY_TEXT = (
    "I'm here to help! Could you please tell me if you're facing an issue with your order, "
    "payment, delivery, or food item?"
)
OFFTOPIC_TEXT = (
    "Sorry! I'm here to help with food orders, menu information, delivery, payments, refunds, "
    "and restaurant-related queries. Please ask me something related to our food services. 😊"
)
LOGIN_TEXT = "Please log in to your Spice Garden account so I can check your order securely. 🔐"

STATUS_HINTS = {
    "placed": "We've received it and will confirm it shortly.",
    "confirmed": "The restaurant has confirmed it and will start preparing soon.",
    "preparing": "Your food is being prepared with care.",
    "ready": "Your order is ready for pickup.",
    "out_for_delivery": "Your delivery partner is on the way.",
    "delivered": "It is marked as delivered. If something is wrong, tell me and I'll help.",
    "cancelled": "This order was cancelled.",
}
REFUND_TEXT = {
    "requested": "Your refund request has been received and is waiting to be processed.",
    "processing": "Your refund is being processed.",
    "completed": "Your refund has been completed.",
    "rejected": "Your refund request was not approved. Please contact support for details.",
}


def _reply(text, intent, order_id=None, quick=None):
    return {"text": text, "intent": intent, "order_id": order_id, "quick": quick or []}


def _find_order_id(raw):
    match = ORDER_ID_RE.search(raw.lower())
    if not match:
        return None
    return int(next(group for group in match.groups() if group))


def _resolve_order(session, user, raw, intent):
    """Returns (order, None) on success or (None, reply) when the customer must be asked something."""
    if user is None:
        return None, _reply(LOGIN_TEXT, intent)
    order_id = _find_order_id(raw)
    if order_id is None:
        session[PENDING_KEY] = {"action": "need_order", "intent": intent}
        session.modified = True
        return None, _reply(
            "I'm sorry for the trouble. Could you please share your order ID? "
            "You can find it under My Orders.", intent,
        )
    order = Order.objects.filter(pk=order_id, user=user).first()
    if order is None:
        return None, _reply("I couldn't find that order on your account. Please double-check the order ID.", intent)
    return order, None


def _items_line(order):
    names = [f"{item.quantity} x {item.name}" for item in order.items.all()]
    return f"Items: {', '.join(names)}." if names else ""


def _open_ticket(user, order, subject, text):
    return SupportTicket.objects.create(user=user, order=order, subject=subject[:120], description=text[:1000])


def _track(session, user, raw):
    order, error = _resolve_order(session, user, raw, "track_order")
    if error:
        return error
    text = (f"Order #{order.pk} is currently: {order.get_status_display()}. "
            f"{STATUS_HINTS[order.status]} {_items_line(order)}").strip()
    return _reply(text, "track_order", order.pk)


def _delayed(session, user, raw):
    order, error = _resolve_order(session, user, raw, "delayed_order")
    if error:
        return error
    text = (f"I'm sorry your food is taking longer than expected. I understand how frustrating that can be. "
            f"Order #{order.pk} is currently: {order.get_status_display()}. {STATUS_HINTS[order.status]}")
    return _reply(text, "delayed_order", order.pk)


def _not_received(session, user, raw):
    order, error = _resolve_order(session, user, raw, "not_received")
    if error:
        return error
    if order.status == "delivered":
        ticket = _open_ticket(user, order, "Marked delivered but not received", raw)
        text = (f"I'm sorry you haven't received your order. Our records show order #{order.pk} as delivered, "
                f"so I've raised support ticket #{ticket.pk} for our team to look into.")
    else:
        text = (f"I'm sorry you haven't received your order yet. Order #{order.pk} is currently: "
                f"{order.get_status_display()}. {STATUS_HINTS[order.status]}")
    return _reply(text, "not_received", order.pk)


def _complaint_handler(intent, subject, intro):
    def handler(session, user, raw):
        order, error = _resolve_order(session, user, raw, intent)
        if error:
            return error
        ticket = _open_ticket(user, order, subject, raw)
        text = (f"{intro} I've raised support ticket #{ticket.pk} for order #{order.pk}. "
                "If you can, please also tell me the item name. Our team will review it.")
        return _reply(text, intent, order.pk)
    return handler


def _refund(session, user, raw):
    order, error = _resolve_order(session, user, raw, "refund_status")
    if error:
        return error
    refund = Refund.objects.filter(order=order).order_by("-created_at").first()
    if refund is None:
        text = (f"I don't see a refund request for order #{order.pk} yet. If you were charged for an "
                "order that was cancelled, I can raise a support ticket for you.")
        return _reply(text, "refund_status", order.pk)
    text = (f"Refund for order #{order.pk}: ₹{refund.amount}. {REFUND_TEXT[refund.status]} "
            "I can't confirm an exact date until our system shows one.")
    return _reply(text, "refund_status", order.pk)


def _payment(session, user, raw):
    order, error = _resolve_order(session, user, raw, "payment_issue")
    if error:
        return error
    payment = Payment.objects.filter(order=order).first()
    if payment is None:
        return _reply(f"I don't see a payment record for order #{order.pk} yet.", "payment_issue", order.pk)
    text = (f"Payment for order #{order.pk}: ₹{payment.amount} via {payment.get_method_display()}. "
            f"Status: {payment.get_status_display()}. Reference: {payment.reference}.")
    if payment.method == Order.PaymentMethod.COD:
        text += " This is cash on delivery, so please pay the delivery partner when your order arrives."
    if payment.status == Order.PaymentStatus.FAILED or "deduct" in raw.lower():
        ticket = _open_ticket(user, order, "Payment issue", raw)
        text += (f" I'm sorry for the trouble. If money was deducted, your bank usually reverses it. "
                 f"I've raised support ticket #{ticket.pk} so our team can verify it.")
    return _reply(text, "payment_issue", order.pk)


def _cancel(session, user, raw):
    order, error = _resolve_order(session, user, raw, "cancel_order")
    if error:
        return error
    if not order.is_cancellable:
        return _reply(f"Order #{order.pk} is already {order.get_status_display().lower()} and can't be "
                      "cancelled now.", "cancel_order")
    session[PENDING_KEY] = {"action": "confirm_cancel", "order_id": order.pk}
    session.modified = True
    return _reply(f"Are you sure you want to cancel order #{order.pk}? Reply YES to confirm or NO to keep it.",
                  "cancel_order", quick=["Yes, cancel it", "No, keep it"])


def _do_cancel(user, order_id):
    order = Order.objects.filter(pk=order_id, user=user).first()
    if order is None:
        return _reply("I couldn't find that order on your account.", "cancel_order")
    try:
        refund_created = cancel_order(order)
    except ValueError as exc:
        return _reply(str(exc), "cancel_order")
    text = f"Your order #{order.pk} has been cancelled."
    if refund_created:
        text += f" A refund request of ₹{order.total} has been created. I'll help you track it."
    return _reply(text, "cancel_order", order.pk)


def _menu_for_foods(foods):
    lines = [
        f"{item.name}: ₹{item.price} - {'available now' if item.is_available else 'currently unavailable'}"
        for item in foods[:5]
    ]
    return _reply("\n".join(lines), "menu_info")


def _menu_general(session, user, raw):
    names = ", ".join(Category.objects.values_list("name", flat=True))
    text = (f"We serve: {names}. Ask me about any dish, for example 'biryani price'." if names
            else "Our menu is being updated. Please check back soon!")
    return _reply(text, "menu_info")


def _offers(session, user, raw):
    coupons = Coupon.objects.filter(active=True)
    if not coupons:
        return _reply("There are no active offers right now. Please check back soon!", "offers")
    lines = [f"{c.code}: {c.description or 'Discount on your order'}" for c in coupons]
    return _reply("Current offers:\n" + "\n".join(lines) + "\nApply a code in your cart at checkout.", "offers")


def _delivery_info(session, user, raw):
    tax_percent = int(settings.TAX_RATE * 100)
    text = (f"The delivery charge is ₹{settings.DELIVERY_FEE}. Delivery is free on orders of "
            f"₹{settings.FREE_DELIVERY_ABOVE} or more. Tax is {tax_percent}% on the order value.")
    return _reply(text, "delivery_info")


def _restaurant_info(session, user, raw):
    text = (f"{settings.RESTAURANT_NAME} is open {settings.RESTAURANT_HOURS}. "
            f"Address: {settings.RESTAURANT_ADDRESS}. You can reach us at {settings.SUPPORT_PHONE} "
            f"or {settings.SUPPORT_EMAIL}.")
    return _reply(text, "restaurant_info")


def _support(session, user, raw):
    if user is None:
        text = (f"You can reach our team at {settings.SUPPORT_EMAIL} or {settings.SUPPORT_PHONE}. "
                "If you log in, I can also raise a support ticket for you.")
        return _reply(text, "support")
    ticket = _open_ticket(user, None, "Customer requested support", raw)
    text = (f"I've raised support ticket #{ticket.pk} for you. Our team will review your request. "
            f"You can also reach us at {settings.SUPPORT_EMAIL} or {settings.SUPPORT_PHONE}.")
    return _reply(text, "support")


def _greeting(session, user, raw):
    return _reply("Hello! 👋 I'm Spice Bot. I can help with orders, payments, refunds and our menu. "
                  "What can I do for you today?", "greeting")


def _thanks(session, user, raw):
    return _reply("You're welcome! Enjoy your meal 😊 Is there anything else I can help with?", "thanks")


HANDLERS = {
    "cancel_order": _cancel,
    "refund_status": _refund,
    "payment_issue": _payment,
    "wrong_item": _complaint_handler("wrong_item", "Wrong item received",
                                     "I'm sorry you received the wrong item."),
    "missing_item": _complaint_handler("missing_item", "Missing item", "I'm sorry an item was missing."),
    "food_quality": _complaint_handler("food_quality", "Food quality issue",
                                       "I'm sorry your food didn't meet your expectations."),
    "not_received": _not_received,
    "delayed_order": _delayed,
    "track_order": _track,
    "delivery_info": _delivery_info,
    "restaurant_info": _restaurant_info,
    "offers": _offers,
    "menu_info": _menu_general,
    "support": _support,
    "greeting": _greeting,
    "thanks": _thanks,
}


def _handle_pending(session, pending, raw, norm, tokens, user):
    """Handles follow-ups such as a missing order ID or a YES/NO confirmation. Returns None to fall through."""
    action = pending.get("action")
    if action == "need_order":
        session.pop(PENDING_KEY, None)
        if _find_order_id(raw) and nlp.match_intent(norm) is None:
            return HANDLERS[pending["intent"]](session, user, raw)
        return None

    if action == "confirm_cancel":
        session.pop(PENDING_KEY, None)
        if nlp.has_any(tokens, nlp.NO_WORDS):
            return _reply(f"No problem! Order #{pending['order_id']} is still active.", "cancel_order")
        if nlp.has_any(tokens, nlp.YES_WORDS):
            return _do_cancel(user, pending["order_id"])
        return None

    if action == "feedback":
        session.pop(PENDING_KEY, None)
        if nlp.has_any(tokens, nlp.YES_WORDS):
            return _reply("Thank you for your feedback! Happy to help any time. 😊", "feedback")
        if nlp.has_any(tokens, nlp.NO_WORDS):
            return _reply("Thanks for letting me know, and I'm sorry I couldn't fully help. "
                          "Would you like me to raise a support ticket? Just type 'support'.", "feedback")
        return None

    session.pop(PENDING_KEY, None)
    return None


def handle_message(request, raw):
    session = request.session
    user = request.user if request.user.is_authenticated else None

    if safety.is_suspicious(raw):
        return _reply(safety.SAFE_REPLY, "blocked")

    norm, tokens = nlp.normalize(raw)

    pending = session.get(PENDING_KEY)
    if pending:
        result = _handle_pending(session, pending, raw, norm, tokens, user)
        if result is not None:
            return result

    intent = nlp.match_intent(norm)

    if intent in (None, "menu_info"):
        foods = nlp.find_food(tokens, norm, list(FoodItem.objects.all()))
        if foods:
            return _menu_for_foods(foods)

    if intent is None:
        if nlp.looks_offtopic(tokens):
            return _reply(OFFTOPIC_TEXT, "off_topic")
        ai_text = ai.ask(raw) if len(tokens) >= 3 else None
        if ai_text:
            return _reply(ai_text, "ai_assist")
        return _reply(CLARIFY_TEXT, "unclear")

    handler = HANDLERS.get(intent)
    if handler is None:
        return _reply(CLARIFY_TEXT, "unclear")

    reply = handler(session, user, raw)
    if reply["order_id"] and intent in FEEDBACK_INTENTS:
        session[PENDING_KEY] = {"action": "feedback"}
        session.modified = True
        reply["text"] += " Was this helpful? 😊"
        reply["quick"] = ["Yes", "No"]
    return reply
