import uuid
from decimal import Decimal

from django.conf import settings
from yookassa import Configuration, Payment


class YookassaNotConfigured(Exception):
    """Не заданы YOOKASSA_SHOP_ID / YOOKASSA_API_KEY."""


class YookassaService:
    def __init__(self):
        self.shop_id = getattr(settings, "YOOKASSA_SHOP_ID", "")
        self.api_key = getattr(settings, "YOOKASSA_API_KEY", "")
        if not self.shop_id or not self.api_key:
            raise YookassaNotConfigured("Платежи не настроены на сервере.")

        Configuration.account_id = self.shop_id
        Configuration.secret_key = self.api_key

    def create_payment(
        self,
        amount: Decimal,
        description: str,
        return_url: str,
        user_id: int,
        *,
        idempotence_key: str | None = None,
        customer_email: str = "",
    ):
        """Создаёт платёж; способ оплаты (карта, СБП и т.д.) клиент выбирает на странице ЮKassa."""
        value = f"{Decimal(amount):.2f}"
        payment_data = {
            "amount": {"value": value, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description[:128],
            "metadata": {"user_id": str(user_id)},
        }

        if getattr(settings, "YOOKASSA_SEND_RECEIPT", False) and customer_email:
            receipt = {
                "customer": {"email": customer_email},
                "items": [
                    {
                        "description": description[:128],
                        "quantity": "1.00",
                        "amount": {"value": value, "currency": "RUB"},
                        "vat_code": settings.YOOKASSA_VAT_CODE,
                        "payment_mode": "full_payment",
                        "payment_subject": "service",
                    }
                ],
            }
            if settings.YOOKASSA_TAX_SYSTEM_CODE:
                receipt["tax_system_code"] = int(settings.YOOKASSA_TAX_SYSTEM_CODE)
            payment_data["receipt"] = receipt

        return Payment.create(payment_data, idempotence_key or str(uuid.uuid4()))

    def get_payment(self, payment_id: str):
        return Payment.find_one(payment_id)
