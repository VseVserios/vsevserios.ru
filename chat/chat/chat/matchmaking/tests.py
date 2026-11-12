from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.billing import get_subscription
from accounts.models import User, WalletTransaction

from .forms import ClientSearchOrderForm
from .models import AdminSearchOrder, Match, Swipe, UserRecommendation
from .services import OrderError, activate_admin_search, record_swipe, request_admin_search


def make_user(username, balance="0", **kwargs):
    now = timezone.now()
    return User.objects.create_user(
        username=username,
        password="pass12345",
        email=f"{username}@example.com",
        email_verified=True,
        terms_accepted_at=now,
        privacy_accepted_at=now,
        wallet_balance=Decimal(balance),
        **kwargs,
    )


def expire_trial(user):
    sub = get_subscription(user)
    sub.trial_ends_at = timezone.now() - timezone.timedelta(days=1)
    sub.save()


class CompatibilityPaywallTests(TestCase):
    def setUp(self):
        self.me = make_user("me")
        self.other = make_user("other")
        self.rec = UserRecommendation.objects.create(
            to_user=self.me, recommended_user=self.other, score=70, is_self_search=True)
        self.client.force_login(self.me)
        self.url = reverse("recommendation_compatibility", args=[self.other.id])

    def test_free_month_shows_details(self):
        response = self.client.get(self.url)
        self.assertFalse(response.context["paywalled"] if "paywalled" in response.context else False)
        self.assertContains(response, "compatChartAtoB")

    def test_after_trial_only_overall_percent(self):
        expire_trial(self.me)
        response = self.client.get(self.url)
        self.assertTrue(response.context["paywalled"])
        self.assertNotContains(response, "compatChartAtoB")
        self.assertEqual(response.context["sections"], [])

    def test_paywall_applies_to_non_self_search_recommendations_too(self):
        UserRecommendation.objects.all().update(is_self_search=False)
        expire_trial(self.me)
        self.assertTrue(self.client.get(self.url).context["paywalled"])

    def test_excel_blocked_after_trial(self):
        expire_trial(self.me)
        response = self.client.get(reverse("recommendation_excel", args=[self.other.id]))
        self.assertRedirects(response, self.url)

    def test_admin_order_recommendation_is_open(self):
        expire_trial(self.me)
        order = AdminSearchOrder.objects.create(
            client=self.me, tier="surface", status=AdminSearchOrder.Status.ACTIVE)
        UserRecommendation.objects.all().update(order=order, is_self_search=False)
        response = self.client.get(self.url)
        self.assertNotIn("paywalled", response.context)

    def test_cancelled_order_does_not_unlock(self):
        expire_trial(self.me)
        order = AdminSearchOrder.objects.create(
            client=self.me, tier="surface", status=AdminSearchOrder.Status.CANCELLED)
        UserRecommendation.objects.all().update(order=order, is_self_search=False)
        self.assertTrue(self.client.get(self.url).context["paywalled"])


class SwipeBillingTests(TestCase):
    def setUp(self):
        self.client_user = make_user("client", balance="1000")
        self.candidate = make_user("cand")
        self.order = AdminSearchOrder.objects.create(
            client=self.client_user, tier="surface", status=AdminSearchOrder.Status.ACTIVE)
        UserRecommendation.objects.create(
            to_user=self.client_user, recommended_user=self.candidate, order=self.order)

    def balance(self):
        self.client_user.refresh_from_db()
        return self.client_user.wallet_balance

    def test_swipe_view_works(self):
        self.client.force_login(self.client_user)
        response = self.client.post(reverse("swipe", args=[self.candidate.id, "like"]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Swipe.objects.filter(from_user=self.client_user).exists())

    def test_charged_once_on_mutual_like(self):
        record_swipe(from_user=self.client_user, to_user=self.candidate, value="like")
        self.assertEqual(self.balance(), Decimal("1000"))
        record_swipe(from_user=self.candidate, to_user=self.client_user, value="like")
        self.assertEqual(self.balance(), Decimal("500"))
        record_swipe(from_user=self.candidate, to_user=self.client_user, value="like")
        record_swipe(from_user=self.client_user, to_user=self.candidate, value="like")
        self.assertEqual(self.balance(), Decimal("500"))
        self.assertEqual(Match.objects.count(), 1)

    def test_charged_when_client_likes_last(self):
        record_swipe(from_user=self.candidate, to_user=self.client_user, value="like")
        record_swipe(from_user=self.client_user, to_user=self.candidate, value="like")
        self.assertEqual(self.balance(), Decimal("500"))

    def test_cancelled_order_not_charged(self):
        self.order.status = AdminSearchOrder.Status.CANCELLED
        self.order.save()
        record_swipe(from_user=self.candidate, to_user=self.client_user, value="like")
        record_swipe(from_user=self.client_user, to_user=self.candidate, value="like")
        self.assertEqual(self.balance(), Decimal("1000"))

    def test_five_rejections_compensation(self):
        for i in range(5):
            cand = make_user(f"c{i}")
            UserRecommendation.objects.create(
                to_user=self.client_user, recommended_user=cand, order=self.order)
            record_swipe(from_user=self.client_user, to_user=cand, value="pass")
        self.assertEqual(self.balance(), Decimal("500"))
        self.assertEqual(
            WalletTransaction.objects.filter(reason=WalletTransaction.Reason.ADMIN_SEARCH).count(), 1)

    def test_admin_is_never_charged(self):
        boss = make_user("boss", balance="1000", is_staff=True)
        order = AdminSearchOrder.objects.create(
            client=boss, tier="surface", status=AdminSearchOrder.Status.ACTIVE)
        UserRecommendation.objects.create(to_user=boss, recommended_user=self.candidate, order=order)
        record_swipe(from_user=self.candidate, to_user=boss, value="like")
        record_swipe(from_user=boss, to_user=self.candidate, value="like")
        boss.refresh_from_db()
        self.assertEqual(boss.wallet_balance, Decimal("1000"))


class AdminSearchOrderTests(TestCase):
    def setUp(self):
        self.user = make_user("client", balance="600")

    def test_request_requires_balance(self):
        poor = make_user("poor", balance="100")
        with self.assertRaises(OrderError):
            request_admin_search(poor, tier="surface", required_criteria="")

    def test_request_then_activate(self):
        order = request_admin_search(self.user, tier="surface", required_criteria="")
        self.assertEqual(order.status, AdminSearchOrder.Status.REQUESTED)
        self.assertEqual(order.price, Decimal("500"))
        activate_admin_search(order)
        order.refresh_from_db()
        self.assertEqual(order.status, AdminSearchOrder.Status.ACTIVE)
        with self.assertRaises(OrderError):
            activate_admin_search(order)

    def test_activation_rechecks_balance(self):
        order = request_admin_search(self.user, tier="surface", required_criteria="")
        self.user.wallet_balance = Decimal("0")
        self.user.save()
        with self.assertRaises(OrderError):
            activate_admin_search(order)

    def test_duplicate_open_order_rejected(self):
        request_admin_search(self.user, tier="surface", required_criteria="")
        with self.assertRaises(OrderError):
            request_admin_search(self.user, tier="surface", required_criteria="")

    def test_staff_cannot_order(self):
        boss = make_user("boss", balance="9999", is_staff=True)
        with self.assertRaises(OrderError):
            request_admin_search(boss, tier="surface", required_criteria="")

    def test_targeted_needs_two_criteria(self):
        form = ClientSearchOrderForm({"tier": "targeted", "required_criteria": "один"})
        self.assertFalse(form.is_valid())
        form = ClientSearchOrderForm({"tier": "targeted", "required_criteria": "один\nдва"})
        self.assertTrue(form.is_valid())

    def test_client_page_flow(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("admin_search")).status_code, 200)
        response = self.client.post(
            reverse("admin_search"), {"tier": "surface", "required_criteria": ""})
        self.assertRedirects(response, reverse("admin_search"))
        order = AdminSearchOrder.objects.get()
        self.client.post(reverse("admin_search_cancel", args=[order.id]))
        order.refresh_from_db()
        self.assertEqual(order.status, AdminSearchOrder.Status.CANCELLED)

    def test_staff_redirected_from_client_page(self):
        boss = make_user("boss", is_staff=True)
        self.client.force_login(boss)
        self.assertRedirects(self.client.get(reverse("admin_search")), reverse("feed"),
                             fetch_redirect_response=False)

    def test_panel_activate(self):
        boss = make_user("boss", is_staff=True, is_superuser=True)
        order = request_admin_search(self.user, tier="surface", required_criteria="")
        self.client.force_login(boss)
        self.client.post(reverse("panel_user_search_order_activate", args=[order.id]))
        order.refresh_from_db()
        self.assertEqual(order.status, AdminSearchOrder.Status.ACTIVE)
