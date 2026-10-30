"""Dashboard helpers: formatting, and that data-driven text can't inject HTML."""
from datetime import date

from app.services.alerts import Alert
from app.services.subscriptions import Subscription
from dashboard import theme
from dashboard.format import money, pretty


def test_money_uses_a_true_minus_before_the_dollar_sign():
    assert money(1234.5) == "$1,234.50"
    assert money(-9.99) == "−$9.99"


def test_pretty_category_names():
    assert pretty("FOOD_AND_DRINK") == "Food & drink"
    assert pretty("RENT_AND_UTILITIES") == "Rent & utilities"


def test_short_date_works_without_platform_specific_strftime():
    assert theme.short_date(date(2026, 11, 4)) == "Nov 4"


def _capture(monkeypatch) -> list[str]:
    out: list[str] = []
    monkeypatch.setattr(theme.st, "html", out.append)
    return out


EVIL = '<img src=x onerror="alert(1)">'


def test_alerts_escape_merchant_text(monkeypatch):
    out = _capture(monkeypatch)
    theme.alert_list([Alert(level="warning", title=f"Unusual charge: {EVIL}", detail=EVIL)])
    assert "<img" not in out[0] and "&lt;img" in out[0]


def test_subscriptions_escape_merchant_text(monkeypatch):
    out = _capture(monkeypatch)
    theme.subscription_list([Subscription(merchant=EVIL, amount=9.99, category="ENTERTAINMENT", times_seen=3,
                                          last_charged="2026-10-01", next_expected="2026-11-01", yearly_cost=119.88)],
                            money, pretty)
    assert "<img" not in out[0]
