from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    emoji = models.CharField(max_length=8, default="🍽️")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FoodItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    ingredients = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.0)
    is_veg = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    image = models.ImageField(upload_to="food/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category__sort_order", "name"]
        indexes = [models.Index(fields=["is_available", "is_popular"])]
        constraints = [
            models.UniqueConstraint(fields=["category", "name"], name="unique_food_per_category"),
        ]

    def __str__(self):
        return self.name
