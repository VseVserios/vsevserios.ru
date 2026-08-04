from django.db import models
from django.conf import settings
import json
import base64


class EncryptedEmailField(models.EmailField):
    """Email field that stores encrypted value in database."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            decrypted = settings.FERNET.decrypt(value.encode())
            return decrypted.decode()
        except Exception:
            return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str):
            return value
        return str(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        if not isinstance(value, str):
            value = str(value)
        encrypted = settings.FERNET.encrypt(value.encode())
        return encrypted.decode()


class EncryptedJSONField(models.JSONField):
    """JSON field that stores encrypted value in database."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            decrypted = settings.FERNET.decrypt(value.encode())
            return json.loads(decrypted.decode())
        except Exception:
            return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                # Try to decrypt if it's an encrypted string
                decrypted = settings.FERNET.decrypt(value.encode())
                return json.loads(decrypted.decode())
            except Exception:
                # If decryption fails, try to parse as JSON directly
                try:
                    return json.loads(value)
                except Exception:
                    # Return as-is if it's not JSON
                    return value
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        json_str = json.dumps(value, ensure_ascii=False)
        encrypted = settings.FERNET.encrypt(json_str.encode())
        return encrypted.decode()
