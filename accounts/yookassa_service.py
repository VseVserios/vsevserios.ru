from decimal import Decimal
from django.conf import settings
from yookassa import Configuration, Payment
from yookassa.domain.common import PaymentMethodType


class YookassaService:
    def __init__(self):
        self.shop_id = getattr(settings, "YOOKASSA_SHOP_ID", "1499327")
        self.api_key = getattr(settings, "YOOKASSA_API_KEY", "")
        self.sbp_legal_id = getattr(settings, "YOOKASSA_SBP_LEGAL_ID", "")
        self.sbp_merchant_id = getattr(settings, "YOOKASSA_SBP_MERCHANT_ID", "")
        self.sbp_mcc = getattr(settings, "YOOKASSA_SBP_MCC", "7273")

        Configuration.account_id = self.shop_id
        Configuration.secret_key = self.api_key

    def create_payment(self, amount: Decimal, description: str, return_url: str, user_id: int):
        """
        Создаёт платёж в ЮKassa с поддержкой СБП
        """
        payment_data = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id)
            }
        }

        # Добавляем методы оплаты с СБП
        payment_data["payment_method_data"] = {
            "type": PaymentMethodType.sberbank,
            "sberbank": {
                "legal_id": self.sbp_legal_id,
                "merchant_id": self.sbp_merchant_id,
                "mcc": self.sbp_mcc
            }
        }

        try:
            payment = Payment.create(payment_data)
            return payment
        except Exception as e:
            raise Exception(f"Ошибка создания платежа: {str(e)}")

    def get_payment(self, payment_id: str):
        """
        Получает информацию о платеже по ID
        """
        try:
            payment = Payment.find_one(payment_id)
            return payment
        except Exception as e:
            raise Exception(f"Ошибка получения платежа: {str(e)}")
