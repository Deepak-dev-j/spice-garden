from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(r"^\+?\d{10,13}$", "Enter a valid phone number (10-13 digits).")
pincode_validator = RegexValidator(r"^\d{6}$", "Enter a valid 6-digit pincode.")


class Address(models.Model):
    class Label(models.TextChoices):
        HOME = "home", "Home"
        WORK = "work", "Work"
        OTHER = "other", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=10, choices=Label.choices, default=Label.HOME)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15, validators=[phone_validator])
    line1 = models.CharField("Address line", max_length=200)
    landmark = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=80)
    pincode = models.CharField(max_length=6, validators=[pincode_validator])
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def as_text(self):
        parts = [self.line1, self.landmark, self.city, self.pincode]
        return ", ".join(p for p in parts if p)

    def __str__(self):
        return f"{self.full_name} - {self.city}"
