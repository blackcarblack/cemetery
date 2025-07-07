
from django.forms import CharField, ModelForm, PasswordInput, ValidationError, Textarea, TextInput, NumberInput, HiddenInput
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .models import Product

User = get_user_model()

class UserRegistrationForm(ModelForm):
    password = CharField(widget=PasswordInput, label="Пароль")
    confirm_password = CharField(widget=PasswordInput, label="Підтвердіть пароль")
    captcha = CharField(widget=HiddenInput(), label="", required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'age', 'country', 'address']
        widgets = {
            'username': TextInput(attrs={'class': 'form-input'}),
            'email': TextInput(attrs={'class': 'form-input'}),
            'age': NumberInput(attrs={'class': 'form-input'}),
            'country': TextInput(attrs={'class': 'form-input'}),
            'address': Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    def clean_captcha(self):
        captcha_token = self.cleaned_data.get('captcha')
        if captcha_token != 'DOOM_CAPTCHA_PASSED':
            raise ValidationError("Будь ласка, пройдіть CAPTCHA.")
        return captcha_token

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Паролі не співпадають")
        
        return cleaned_data


class AdminRegistrationForm(UserRegistrationForm):
    class Meta(UserRegistrationForm.Meta):
        fields = UserRegistrationForm.Meta.fields
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = CharField(widget=TextInput(attrs={'class': 'form-input', 'placeholder': 'Ім\'я користувача'}))
    password = CharField(widget=PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Пароль'}))


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description']
        widgets = {
            'name': TextInput(attrs={'class': 'form-input'}),
            'price': NumberInput(attrs={'class': 'form-input'}),
            'description': Textarea(attrs={'class': 'form-input'}),
        }
