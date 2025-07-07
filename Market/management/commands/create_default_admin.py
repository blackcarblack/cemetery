from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Створює адміністратора за замовчуванням, якщо жодного не існує'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('Адміністратор вже існує'))
            return

        # Створюємо адміністратора за замовчуванням
        admin_username = 'admin'
        admin_password = 'admin123'
        admin_email = 'admin@example.com'
        
        admin = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'Адміністратор створений успішно!\n'
            f'Логін: {admin_username}\n'
            f'Пароль: {admin_password}\n'
            f'Email: {admin_email}\n'
            f'ВАЖЛИВО: Змініть пароль після першого входу!'
        ))