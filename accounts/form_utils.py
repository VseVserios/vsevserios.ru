# Form utilities and enhancements

from django import forms
from django.core.exceptions import ValidationError
import re


class EnhancedForm(forms.Form):
    """Базовый класс для улучшенных форм с встроенной валидацией"""
    
    def clean_email(self):
        """Валидирует email поле"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError('Email обязателен')
        
        # Базовая проверка формата
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Некорректный формат email')
        
        return email
    
    def clean_username(self):
        """Валидирует username поле"""
        username = self.cleaned_data.get('username', '').strip()
        
        if not username:
            raise ValidationError('Имя пользователя обязательно')
        
        if len(username) < 3:
            raise ValidationError('Имя пользователя должно быть не менее 3 символов')
        
        if len(username) > 150:
            raise ValidationError('Имя пользователя не должно быть больше 150 символов')
        
        # Только буквы, цифры, точки, дефисы и подчеркивания
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            raise ValidationError('Имя пользователя может содержать только буквы, цифры и символы . _ -')
        
        return username
    
    def clean_phone(self):
        """Валидирует телефон"""
        phone = self.cleaned_data.get('phone', '')
        
        if phone:
            # Оставить только цифры
            digits = re.sub(r'\D', '', phone)
            if len(digits) < 10:
                raise ValidationError('Некорректный номер телефона')
        
        return phone
    
    def clean_url(self):
        """Валидирует URL"""
        url = self.cleaned_data.get('url', '').strip()
        
        if url:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
                r'(?::\d+)?'  # port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(url):
                raise ValidationError('Некорректный URL')
        
        return url


def get_form_errors(form):
    """Получить все ошибки формы в удобном формате"""
    errors = {}
    for field, field_errors in form.errors.items():
        errors[field] = list(field_errors)
    return errors


def apply_form_css_classes(form, css_class='form-control'):
    """Применяет CSS класс ко всем полям формы"""
    for field in form.fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = 'form-checkbox'
        elif isinstance(field.widget, forms.RadioSelect):
            field.widget.attrs['class'] = 'form-radio'
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = f'{css_class} form-select'
        elif isinstance(field.widget, forms.Textarea):
            field.widget.attrs['class'] = f'{css_class} textarea'
        else:
            field.widget.attrs['class'] = css_class
    
    return form


class ConfirmPasswordMixin:
    """Миксин для проверки совпадения паролей"""
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1', '').strip()
        password2 = cleaned_data.get('password2', '').strip()
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Пароли не совпадают')
        
        return cleaned_data


class PasswordValidationMixin:
    """Миксин для валидации качества пароля"""
    
    MIN_PASSWORD_LENGTH = 8
    
    def clean_password(self):
        """Валидирует пароль"""
        password = self.cleaned_data.get('password', '')
        
        if not password:
            raise ValidationError('Пароль обязателен')
        
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f'Пароль должен быть не менее {self.MIN_PASSWORD_LENGTH} символов'
            )
        
        # Проверка на пустоту
        if not password.strip():
            raise ValidationError('Пароль не может состоять только из пробелов')
        
        # Предупреждение о слабом пароле
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*' for c in password)
        
        strength = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength < 2:
            raise ValidationError(
                'Используйте прописные буквы, цифры и специальные символы для безопасности'
            )
        
        return password


class BioValidationMixin:
    """Миксин для валидации биографии"""
    
    MAX_BIO_LENGTH = 500
    
    def clean_bio(self):
        """Валидирует биографию"""
        bio = self.cleaned_data.get('bio', '').strip()
        
        if len(bio) > self.MAX_BIO_LENGTH:
            raise ValidationError(
                f'Биография не должна быть больше {self.MAX_BIO_LENGTH} символов'
            )
        
        # Проверка на спам
        spam_words = ['casino', 'porn', 'xxx']  # Примеры
        if any(word.lower() in bio.lower() for word in spam_words):
            raise ValidationError('Биография содержит недопустимый контент')
        
        return bio


class ImageValidationMixin:
    """Миксин для валидации изображений"""
    
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    
    def clean_image(self):
        """Валидирует изображение"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Проверка расширения
            ext = image.name.split('.')[-1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f'Допустимые форматы: {", ".join(self.ALLOWED_EXTENSIONS)}'
                )
            
            # Проверка размера
            if image.size > self.MAX_IMAGE_SIZE:
                raise ValidationError(
                    f'Размер изображения не должен превышать 5MB'
                )
        
        return image
