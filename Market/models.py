from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, AbstractUser
from django.db.models import CharField, DateField, IntegerField, BooleanField, FloatField, Model, EmailField, TextField, \
    ImageField, DateTimeField, ForeignKey, CASCADE
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
class CustomUser(AbstractUser):
    age = models.IntegerField(null=True, blank=True)  # Removed trailing comma
    country = models.CharField(max_length=100, blank=True)  # Added blank=True
    address = models.TextField(blank=True)  # Added blank=True

    class Meta:
        # Add related_name to avoid conflicts
        db_table = 'market_customuser'

    # Override the groups and user_permissions to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    def __str__(self):
        return self.username


class Product(models.Model):
    SECTION_CHOICES = [
        ('pizza', 'Pizza'),
        ('sushi', 'Sushi'),
        ('salad', 'Salad'),
        ('drink', 'Drink'),
        ('desert', 'Desert'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='other')

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"