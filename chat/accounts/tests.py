import json
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from matchmaking.models import SelfSearchSubscription

from .billing import has_full_analysis_access, purchase_subscription
from .models import User, WalletTransaction, YookassaPayment
from .payments import InvalidAmount, parse_topup_amount, sync_payment
from .wallet import InsufficientFunds

CONFIGURED = dict(YOOKASSA_SHOP_ID="shop", YOOKASSA_API_KEY="key")


def make_user(username="u1", **kwargs):
    now = timezone.now()
    defaults = dict(
        email=f"{username}@example.com",
        email_verified=True,
        terms_accepted_at=now,
        privacy_accepted_at=now,
    )
    defaults.update(kwargs)
    return User.objects.create_user(username=username, password="pass12345", **defaults)


def remote(status="succeeded", amount="500.00", user_id=None, method="bank_card", currency="RUB"):
    return SimpleNamespace(
        id="pay-1",
        status=status,
        amount=SimpleNamespace(value=amount, currency=currency),
        metadata={"user_id": str(user_id)} if user_id is not None else {},
        payment_method=SimpleNamespace(type=method),
        confirmation=SimpleNamespace(confirmation_url="https://yookassa.example/pay"),
    )


def make_payment(user, amount="500.00", payment_id="pay-1"):
    return YookassaPayment.objects.create(
        user=user, payment_id=payment_id, amount=Decimal(amount), currency="RUB")


class TopupAmountTests(TestCase):
    def test_valid(self):
        self.assertEqual(parse_topup_amount("150,5"), Decimal("150.50"))

    def test_invalid(self):
        for raw in ["", "abc", "NaN", "Infinity", "-5", "0", "99", "100001"]:
            with self.assertRaises(InvalidAmount, msg=raw):
                parse_topup_amount(raw)


@override_settings(**CONFIGURED)
class PaymentFlowTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_fake_topup_endpoint_is_gone(self):
        response = self.client.post("/accounts/payment/topup/", {"amount": "1000"})
        self.assertEqual(response.status_code, 404)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, 0)

    def test_create_payment_redirects_to_yookassa(self):
        with mock.patch("accounts.payments.YookassaService") as svc:
            svc.return_value.create_payment.return_value = remote(status="pending")
            response = self.client.post(reverse("yookassa_create_payment"), {"amount": "500"})
        self.assertRedirects(response, "https://yookassa.example/pay", fetch_redirect_response=False)
        payment = YookassaPayment.objects.get()
        self.assertEqual(payment.amount, Decimal("500.00"))
        self.assertEqual(payment.status, YookassaPayment.Status.PENDING)
        return_url = svc.return_value.create_payment.call_args.kwargs["return_url"]
        self.assertIn(str(payment.public_id), return_url)

    def test_create_payment_rejects_bad_amount(self):
        response = self.client.post(reverse("yookassa_create_payment"), {"amount": "5"})
        self.assertRedirects(response, reverse("payment"))
        self.assertFalse(YookassaPayment.objects.exists())

    def test_success_page_credits_once(self):
        payment = make_payment(self.user)
        url = f"{reverse('yookassa_payment_success')}?p={payment.public_id}"
        with mock.patch("accounts.yookassa_service.Payment.find_one",
                        return_value=remote(user_id=self.user.id)):
            self.client.get(url)
            self.client.get(url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal("500.00"))
        self.assertEqual(WalletTransaction.objects.filter(reason="topup").count(), 1)

    def test_success_page_other_users_payment_not_found(self):
        other = make_user("u2")
        payment = make_payment(other)
        with mock.patch("accounts.yookassa_service.Payment.find_one",
                        return_value=remote(user_id=other.id)):
            self.client.get(f"{reverse('yookassa_payment_success')}?p={payment.public_id}")
        other.refresh_from_db()
        self.assertEqual(other.wallet_balance, 0)

    def test_success_page_garbage_id(self):
        response = self.client.get(f"{reverse('yookassa_payment_success')}?p=not-a-uuid")
        self.assertRedirects(response, reverse("payment"))


@override_settings(**CONFIGURED)
class WebhookTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.payment = make_payment(self.user)
        self.http = Client(enforce_csrf_checks=True)

    def post(self, event="payment.succeeded"):
        body = {"event": event, "object": {"id": "pay-1"}}
        return self.http.post(
            reverse("yookassa_webhook"), data=json.dumps(body), content_type="application/json")

    def test_webhook_works_without_csrf_and_credits(self):
        with mock.patch("accounts.yookassa_service.Payment.find_one",
                        return_value=remote(user_id=self.user.id)):
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal("500.00"))

    def test_forged_webhook_does_not_credit(self):
        with mock.patch("accounts.yookassa_service.Payment.find_one",
                        return_value=remote(status="pending", user_id=self.user.id)):
            self.post()
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, 0)

    def test_webhook_get_not_allowed(self):
        self.assertEqual(self.http.get(reverse("yookassa_webhook")).status_code, 405)

    def test_webhook_invalid_json(self):
        response = self.http.post(
            reverse("yookassa_webhook"), data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_webhook_api_failure_requests_retry(self):
        with mock.patch("accounts.yookassa_service.Payment.find_one", side_effect=RuntimeError):
            self.assertEqual(self.post().status_code, 500)

    def test_sync_rejects_amount_mismatch(self):
        sync_payment("pay-1", remote(amount="1.00", user_id=self.user.id))
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, 0)

    def test_canceled_does_not_override_succeeded(self):
        sync_payment("pay-1", remote(user_id=self.user.id))
        sync_payment("pay-1", remote(status="canceled", user_id=self.user.id))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, YookassaPayment.Status.SUCCEEDED)


class SubscriptionTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.other = make_user("u2")

    def expire_trial(self):
        sub = SelfSearchSubscription.objects.get(user=self.user)
        sub.trial_ends_at = timezone.now() - timezone.timedelta(days=1)
        sub.save()

    def test_trial_then_paywall_then_paid(self):
        self.assertTrue(has_full_analysis_access(self.user, self.other))
        self.expire_trial()
        self.assertFalse(has_full_analysis_access(self.user, self.other))

        with self.assertRaises(InsufficientFunds):
            purchase_subscription(self.user)

        self.user.wallet_balance = Decimal("600")
        self.user.save()
        sub = purchase_subscription(self.user)
        self.assertTrue(sub.paid_until > timezone.now())
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal("100"))
        self.assertTrue(has_full_analysis_access(self.user, self.other))

    def test_staff_never_paywalled_and_cannot_pay(self):
        admin = make_user("boss", is_staff=True)
        self.assertTrue(has_full_analysis_access(admin, self.other))
        self.assertFalse(SelfSearchSubscription.objects.filter(user=admin).exists())

        self.client.force_login(admin)
        for name in ("payment",):
            self.assertRedirects(self.client.get(reverse(name)), reverse("feed"),
                                 fetch_redirect_response=False)
        response = self.client.post(reverse("payment_self_search"))
        self.assertRedirects(response, reverse("feed"), fetch_redirect_response=False)
        response = self.client.post(reverse("yookassa_create_payment"), {"amount": "500"})
        self.assertRedirects(response, reverse("feed"), fetch_redirect_response=False)

    def test_payment_pages_for_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("payment"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Кошелёк")
