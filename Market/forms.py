
from django.forms import CharField, ModelForm, PasswordInput, ValidationError, Textarea, TextInput, NumberInput, \
    HiddenInput, FileInput, Select
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Product, Comment
from django import forms
from captcha.fields import CaptchaField




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





class LoginForm(AuthenticationForm):
    """Форма входу"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].label = 'Ім\'я користувача'
        self.fields['password'].label = 'Пароль'

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'image', 'section']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'price': NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': FileInput(attrs={'class': 'form-control'}),
            'section': Select(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = Comment
        fields = ['name', 'text', 'captcha']
        labels = {
            'name': "Ім'я",
            'text': 'Коментар'
        }

class CheckoutForm(forms.Form):
    name = forms.CharField(label="Ім’я", max_length=100)
    surname = forms.CharField(label="Прізвище", max_length=100)
    phone = forms.CharField(label="Телефон", max_length=20)
    email = forms.EmailField(label="Email")
    address = forms.CharField(label="Адреса доставки", widget=forms.Textarea)
    card_number = forms.CharField(label="Номер картки", max_length=19)
    expiration_date = forms.CharField(label="Термін дії (MM/YY)", max_length=5)
    cvv = forms.CharField(label="CVV", max_length=4)
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)