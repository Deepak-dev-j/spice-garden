from django.contrib import admin

from .models import Category, FoodItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "emoji", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_veg", "is_available", "is_popular", "rating")
    list_editable = ("price", "is_available", "is_popular")
    list_filter = ("category", "is_veg", "is_available", "is_popular")
    search_fields = ("name", "description", "ingredients")
