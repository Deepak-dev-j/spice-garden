import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order

from . import nlp


def intent_of(text):
    norm, _ = nlp.normalize(text)
    return nlp.match_intent(norm)


class NLPTests(TestCase):
    def test_typos_and_informal_language(self):
        self.assertEqual(intent_of("ordr not recived"), "not_received")
        self.assertEqual(intent_of("refund not came"), "refund_status")
        self.assertEqual(intent_of("money cut order not placed"), "payment_issue")
        self.assertEqual(intent_of("cancel ord"), "cancel_order")
        self.assertEqual(intent_of("one item miss"), "missing_item")
        self.assertEqual(intent_of("my order late"), "delayed_order")


class ChatApiTests(TestCase):
    def send(self, message):
        response = self.client.post(
            reverse("chat_message"), data=json.dumps({"message": message}), content_type="application/json"
        )
        return response.json()

    def test_off_topic_is_redirected(self):
        self.assertEqual(self.send("Tell me about Python programming.")["intent"], "off_topic")

    def test_empty_message_is_handled(self):
        self.assertEqual(self.send("   ")["intent"], "empty")

    def test_anonymous_user_must_log_in_for_orders(self):
        result = self.send("where my order")
        self.assertIn("log in", result["reply"].lower())

    def test_customer_cannot_see_another_customers_order(self):
        User = get_user_model()
        owner = User.objects.create_user("owner", password="Str0ng-pass-123")
        other = User.objects.create_user("other", password="Str0ng-pass-456")
        order = Order.objects.create(
            user=owner, customer_name="Owner", phone="9999999999",
            delivery_address="Some address here", total=100, subtotal=100,
        )
        self.client.force_login(other)
        result = self.send(f"where is order {order.pk}")
        self.assertIn("couldn't find", result["reply"])
