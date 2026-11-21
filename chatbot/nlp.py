"""Text normalisation, typo correction, fuzzy food matching and rule-based intent detection."""
import difflib
import re

SYNONYMS = {
    "ordr": "order", "ord": "order", "odr": "order", "ordar": "order", "orderr": "order",
    "recived": "received", "recieved": "received", "recive": "received", "rcvd": "received",
    "refnd": "refund", "refud": "refund", "rfnd": "refund", "rfd": "refund", "refunnd": "refund",
    "pymnt": "payment", "paymnt": "payment", "paymet": "payment", "payement": "payment", "pament": "payment",
    "dlvry": "delivery", "delivey": "delivery", "deliverry": "delivery", "delievery": "delivery",
    "delivry": "delivery", "delivred": "delivered", "deliverd": "delivered",
    "biriyani": "biryani", "briyani": "biryani", "biryni": "biryani", "biriyan": "biryani",
    "pizzza": "pizza", "cancle": "cancel", "canel": "cancel", "cancell": "cancel",
    "misng": "missing", "mising": "missing", "missin": "missing", "miss": "missing",
    "lete": "late", "latee": "late", "wrng": "wrong", "wrnog": "wrong",
    "fod": "food", "fodd": "food", "foood": "food",
    "wher": "where", "whr": "where", "wat": "what", "hw": "how",
    "dont": "not", "dnt": "not", "didnt": "not", "cant": "not", "cnt": "not",
    "amt": "amount", "moni": "money", "mony": "money", "monney": "money",
    "dedected": "deducted", "deducte": "deducted",
    "tkt": "ticket", "hlp": "help", "halp": "help", "helo": "hello", "hii": "hi",
    "menue": "menu", "munu": "menu", "avaliable": "available", "availble": "available", "avilable": "available",
    "pls": "please", "plz": "please", "thx": "thanks", "tq": "thanks", "ur": "your", "u": "you",
}

# Ordered by priority: the first intent whose phrase appears in the message wins.
INTENT_RULES = [
    ("cancel_order", ["cancel", "cancellation", "stop my order", "dont want order", "do not want order"]),
    ("refund_status", ["refund", "money back", "return my money"]),
    ("payment_issue", ["payment", "paid", "money cut", "money deducted", "deducted", "debited",
                       "charged", "transaction", "upi", "not placed", "payment failed"]),
    ("wrong_item", ["wrong", "incorrect", "different item", "not what i ordered", "mistake"]),
    ("missing_item", ["missing", "one item", "item missing", "item not", "forgot", "not included"]),
    ("not_received", ["not received", "not receive", "not came", "not come", "not arrived",
                      "not reached", "not delivered", "did not get", "never came"]),
    ("delayed_order", ["late", "delay", "delayed", "taking long", "too long", "still waiting",
                       "not yet", "slow"]),
    ("food_quality", ["cold", "stale", "quality", "tasteless", "spoiled", "damaged", "packaging",
                      "spilled", "leaked", "bad taste"]),
    ("track_order", ["where", "track", "status", "eta", "when", "on the way", "out for delivery", "update"]),
    ("delivery_info", ["delivery charge", "delivery fee", "delivery time", "delivery cost", "free delivery"]),
    ("restaurant_info", ["open", "opening", "hours", "timing", "address", "location", "branch", "close"]),
    ("offers", ["offer", "discount", "coupon", "promo", "deal", "code"]),
    ("menu_info", ["menu", "price", "cost", "rate", "available", "availability", "ingredient",
                   "veg", "nonveg", "non veg", "dish", "item"]),
    ("support", ["support", "agent", "human", "complaint", "manager", "callback", "call back",
                 "ticket", "talk to someone"]),
    ("greeting", ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "vanakkam"]),
    ("thanks", ["thanks", "thank you", "thank"]),
]

EXTRA_DOMAIN = {
    "order", "orders", "food", "meal", "restaurant", "delivery", "payment", "refund", "menu",
    "item", "items", "bill", "biryani", "pizza", "burger", "dessert", "drink", "price", "help",
    "problem", "issue", "account", "status", "dosa", "idli",
}

PHRASE_WORDS = {word for _, phrases in INTENT_RULES for phrase in phrases for word in phrase.split()}
VOCAB = PHRASE_WORDS | EXTRA_DOMAIN
YES_WORDS = {"yes", "y", "yeah", "yep", "yup", "sure", "confirm", "ok", "okay", "correct"}
NO_WORDS = {"no", "n", "nope", "nah", "keep", "dont", "not", "stop"}


def _correct(token):
    if token in SYNONYMS:
        return SYNONYMS[token]
    if token in VOCAB or len(token) < 4:
        return token
    close = difflib.get_close_matches(token, VOCAB, n=1, cutoff=0.8)
    return close[0] if close else token


def normalize(text):
    """Lowercases, strips symbols and emoji, collapses stretched letters, fixes typos."""
    cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    cleaned = re.sub(r"(.)\1{2,}", r"\1\1", cleaned)
    tokens = [_correct(token) for token in cleaned.split()]
    return " ".join(tokens), tokens


def match_intent(norm):
    padded = f" {norm} "
    for intent, phrases in INTENT_RULES:
        for phrase in phrases:
            if f" {phrase} " in padded:
                return intent
    return None


def find_food(tokens, norm, items):
    found = []
    for item in items:
        name = item.name.lower()
        words = [w for w in re.split(r"\W+", name) if len(w) >= 4]
        if name in norm or any(
            w in tokens or difflib.get_close_matches(w, tokens, n=1, cutoff=0.85) for w in words
        ):
            found.append(item)
    return found


def has_any(tokens, words):
    return any(token in words for token in tokens)


def looks_offtopic(tokens):
    return len(tokens) >= 3 and not any(token in VOCAB for token in tokens)
