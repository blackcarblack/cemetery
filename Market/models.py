from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, AbstractUser

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
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_new = models.BooleanField(default=True, editable=False)

    def save(self, *args, **kwargs):
        if self.created_at:
            self.is_new = timezone.now() - self.created_at <= timedelta(hours=2)
        else:
            self.is_new = True
        super().save(*args, **kwargs)

    @property
    def likes_count(self):
        return self.productrating_set.filter(is_like=True).count()

    @property
    def dislikes_count(self):
        return self.productrating_set.filter(is_like=False).count()

    @property
    def rating_score(self):
        return self.likes_count - self.dislikes_count

    def __str__(self):
        return self.name

class ProductRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user_ip = models.GenericIPAddressField()
    is_like = models.BooleanField()  # True для лайка, False для дизлайка
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{'Like' if self.is_like else 'Dislike'} for {self.product.name}"

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)  # Optional user association
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in cart"