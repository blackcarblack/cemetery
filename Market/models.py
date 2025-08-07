from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, AbstractUser
from django.db.models import CharField, DateField, IntegerField, BooleanField, FloatField, Model, EmailField, TextField, \
    ImageField, DateTimeField, ForeignKey, CASCADE
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from PIL import Image
import os
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
        ('Піца', 'Піца'),
        ('Суші', 'Суші'),
        ('Салати', 'Салати'),
        ('Напої', 'Напої'),
        ('Десерти', 'Десерти'),
    ]

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='pizza')  # <-- додано

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            # Зміна розміру
            max_size = (300, 300)
            img.thumbnail(max_size)

            # Перезаписати файл
            img.save(img_path)

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"

class Comment(Model):
    product = ForeignKey(Product, on_delete=CASCADE, related_name='comments')
    name = CharField(max_length=100)
    text = TextField()
    created_at = DateTimeField(auto_now_add=True)