"""Blocks prompt-injection, SQL, code and data-exposure attempts before any logic runs."""
import re

SAFE_REPLY = (
    "I can only help with Spice Garden food orders, menu, delivery, payments, refunds and support. "
    "How can I help with those? 😊"
)

_SUSPICIOUS = re.compile(
    r"ignore (all |your |the )?(previous|above|prior) |system prompt|your instructions|developer mode"
    r"|drop table|delete from|insert into|union select|select .+ from|<script|__import__"
    r"|exec\(|os\.system|import os|other customers?|another customer's|reveal (your|the) "
    r"|show (me )?(the )?database|api key",
    re.IGNORECASE,
)


def is_suspicious(text):
    return bool(_SUSPICIOUS.search(text))
