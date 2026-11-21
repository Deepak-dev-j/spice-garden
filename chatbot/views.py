import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from . import services
from .models import ChatMessage

logger = logging.getLogger(__name__)
MAX_LENGTH = 500


def _session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


@require_POST
def message(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    text = str(payload.get("message", "")).strip()[:MAX_LENGTH]
    if not text:
        return JsonResponse({
            "reply": "Please type a message so I can help you. 😊",
            "intent": "empty",
            "quick_replies": [],
        })

    key = _session_key(request)
    user = request.user if request.user.is_authenticated else None
    ChatMessage.objects.create(session_key=key, user=user, role=ChatMessage.Role.USER, text=text)

    try:
        result = services.handle_message(request, text)
    except Exception:
        logger.exception("Chatbot failed while handling a message")
        result = {
            "text": "Sorry, something went wrong on my side. Please try again in a moment. 🙏",
            "intent": "error", "order_id": None, "quick": ["Retry"],
        }

    ChatMessage.objects.create(
        session_key=key, user=user, role=ChatMessage.Role.BOT,
        text=result["text"], intent=result["intent"], order_id=result["order_id"],
    )
    return JsonResponse({
        "reply": result["text"],
        "intent": result["intent"],
        "quick_replies": result["quick"],
    })


@require_GET
def history(request):
    key = _session_key(request)
    recent = list(ChatMessage.objects.filter(session_key=key).order_by("-created_at")[:50])
    data = [
        {"role": m.role, "text": m.text, "created_at": m.created_at.isoformat()}
        for m in reversed(recent)
    ]
    return JsonResponse({"messages": data})


@require_POST
def clear(request):
    key = _session_key(request)
    ChatMessage.objects.filter(session_key=key).delete()
    request.session.pop(services.PENDING_KEY, None)
    return JsonResponse({"ok": True})
