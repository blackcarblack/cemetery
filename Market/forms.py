
from django.forms import CharField, ModelForm, PasswordInput, ValidationError, Textarea, TextInput, NumberInput, HiddenInput
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Product

User = get_user_model()


class UserRegistrationForm(ModelForm):
    """Форма реєстрації користувача"""
    password = CharField(
        widget=PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )
    password_confirm = CharField(
        widget=PasswordInput(attrs={'class': 'form-control'}),
        label='Підтвердіть пароль'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': TextInput(attrs={'class': 'form-control'}),
            'email': TextInput(attrs={'class': 'form-control'}),
            'first_name': TextInput(attrs={'class': 'form-control'}),
            'last_name': TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Ім\'я користувача',
            'email': 'Електронна пошта',
            'first_name': 'Ім\'я',
            'last_name': 'Прізвище',
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Паролі не співпадають')
        return password_confirm


class AdminRegistrationForm(ModelForm):
    """Форма реєстрації адміністратора"""
    password = CharField(
        widget=PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )
    password_confirm = CharField(
        widget=PasswordInput(attrs={'class': 'form-control'}),
        label='Підтвердіть пароль'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': TextInput(attrs={'class': 'form-control'}),
            'email': TextInput(attrs={'class': 'form-control'}),
            'first_name': TextInput(attrs={'class': 'form-control'}),
            'last_name': TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Ім\'я користувача',
            'email': 'Електронна пошта',
            'first_name': 'Ім\'я',
            'last_name': 'Прізвище',
        }

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Паролі не співпадають')
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Робимо користувача адміністратором
        user.is_superuser = True
        if commit:
            user.save()
        return user


class ProductForm(ModelForm):
    """Форма товару"""
    class Meta:
        model = Product
        fields = ['name', 'description', 'price']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'name': 'Назва товару',
            'description': 'Опис товару',
            'price': 'Ціна (грн)',
        }


class LoginForm(AuthenticationForm):
    """Форма входу"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].label = 'Ім\'я користувача'
        self.fields['password'].label = 'Пароль'

