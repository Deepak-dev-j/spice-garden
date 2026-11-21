from decimal import Decimal

from django.core.management.base import BaseCommand

from menu.models import Category, FoodItem
from orders.models import Coupon

MENU = [
    ("Biryani", "🍛", [
        ("Chicken Dum Biryani", "Slow-cooked basmati with tender chicken and saffron.", "249", False, True, "4.7"),
        ("Paneer Biryani", "Fragrant rice layered with spiced paneer cubes.", "229", True, True, "4.5"),
        ("Mutton Biryani", "Rich mutton biryani with fried onions and mint.", "329", False, False, "4.6"),
        ("Veg Biryani", "Garden vegetables cooked with aromatic spices.", "199", True, False, "4.2"),
    ]),
    ("Pizza", "🍕", [
        ("Margherita Pizza", "Classic tomato, mozzarella and fresh basil.", "219", True, True, "4.4"),
        ("Peppy Paneer Pizza", "Paneer, capsicum, onion and spicy sauce.", "289", True, False, "4.3"),
        ("Chicken Tikka Pizza", "Smoky tikka chicken with onion and peppers.", "329", False, False, "4.5"),
    ]),
    ("Burgers", "🍔", [
        ("Classic Veg Burger", "Crispy veg patty, lettuce and tangy sauce.", "129", True, False, "4.1"),
        ("Crispy Chicken Burger", "Golden fried chicken with mayo and pickles.", "179", False, True, "4.6"),
    ]),
    ("South Indian", "🥘", [
        ("Masala Dosa", "Crisp dosa stuffed with spiced potato masala.", "89", True, True, "4.7"),
        ("Idli Sambar", "Soft steamed idlis served with sambar and chutney.", "69", True, False, "4.4"),
        ("Medu Vada", "Crispy lentil vada with coconut chutney.", "59", True, False, "4.3"),
        ("Chettinad Chicken", "Peppery chicken curry from Chettinad.", "289", False, False, "4.6"),
    ]),
    ("North Indian", "🫓", [
        ("Butter Chicken", "Creamy tomato gravy with tender chicken pieces.", "299", False, True, "4.8"),
        ("Paneer Butter Masala", "Paneer simmered in a buttery tomato gravy.", "269", True, False, "4.6"),
        ("Garlic Naan", "Tandoor-baked bread brushed with garlic butter.", "49", True, False, "4.5"),
    ]),
    ("Snacks", "🍟", [
        ("French Fries", "Golden, crispy fries with seasoning.", "99", True, False, "4.0"),
        ("Veg Spring Rolls", "Crunchy rolls filled with spiced vegetables.", "149", True, False, "4.2"),
        ("Chicken 65", "Spicy deep-fried chicken bites.", "169", False, True, "4.5"),
    ]),
    ("Desserts", "🍰", [
        ("Gulab Jamun", "Soft milk dumplings soaked in rose syrup.", "79", True, False, "4.5"),
        ("Chocolate Brownie", "Warm fudgy brownie with a rich chocolate finish.", "149", True, True, "4.6"),
    ]),
    ("Beverages", "🥤", [
        ("Masala Chai", "Freshly brewed spiced tea.", "39", True, False, "4.3"),
        ("Mango Lassi", "Chilled yogurt drink blended with real mango.", "99", True, False, "4.6"),
        ("Cold Coffee", "Creamy iced coffee with a hint of chocolate.", "129", True, False, "4.4"),
    ]),
]


class Command(BaseCommand):
    help = "Loads sample categories, food items and coupons (safe to run more than once)."

    def handle(self, *args, **options):
        for order, (cat_name, emoji, items) in enumerate(MENU, start=1):
            category, _ = Category.objects.update_or_create(
                name=cat_name, defaults={"emoji": emoji, "sort_order": order}
            )
            for name, desc, price, veg, popular, rating in items:
                FoodItem.objects.update_or_create(
                    category=category,
                    name=name,
                    defaults={
                        "description": desc,
                        "price": Decimal(price),
                        "is_veg": veg,
                        "is_popular": popular,
                        "rating": Decimal(rating),
                        "is_available": True,
                    },
                )

        Coupon.objects.update_or_create(
            code="WELCOME10",
            defaults={"description": "10% off on orders above ₹199", "percent_off": 10,
                      "min_order": Decimal("199.00"), "active": True},
        )
        Coupon.objects.update_or_create(
            code="FLAT50",
            defaults={"description": "Flat ₹50 off on orders above ₹399", "flat_off": Decimal("50.00"),
                      "min_order": Decimal("399.00"), "active": True},
        )
        self.stdout.write(self.style.SUCCESS("Sample menu and coupons are loaded."))
