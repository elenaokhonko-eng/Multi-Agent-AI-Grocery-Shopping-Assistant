from typing import TypedDict


class MoneyBreakdown(TypedDict):
    gross_total_cents: int
    net_cents: int
    gst_cents: int
    source_currency: str


def calculate_gst_inclusive(
    gross_total_cents: int,
    gst_rate_percent: float = 9.0
) -> MoneyBreakdown:
    """
    Singapore GST is currently 9%. Prices are generally GST-inclusive.
    This extracts the exact GST amount embedded in the gross total.

    Uses standard half-even rounding for tax calculation.
    net + gst = gross
    gst = gross - (gross / (1 + gst_rate_percent / 100))
    """
    if gross_total_cents == 0:
        return {
            "gross_total_cents": 0,
            "net_cents": 0,
            "gst_cents": 0,
            "source_currency": "SGD"
        }

    gst_multiplier = gst_rate_percent / 100.0
    net_float = gross_total_cents / (1 + gst_multiplier)

    # Standard half-even rounding
    net_cents = round(net_float)
    gst_cents = gross_total_cents - net_cents

    return {
        "gross_total_cents": gross_total_cents,
        "net_cents": net_cents,
        "gst_cents": gst_cents,
        "source_currency": "SGD"
    }


def add_money(cents_a: int, cents_b: int) -> int:
    """
    Safely add two integer amounts.
    """
    return cents_a + cents_b


def multiply_money(cents: int, quantity: int) -> int:
    """
    Multiply unit price by quantity.
    """
    return cents * quantity

def calculate_delivery_fee(subtotal_cents: int, free_threshold_cents: int, fee_cents: int) -> int:
    if subtotal_cents >= free_threshold_cents:
        return 0
    return fee_cents

def cents_to_display(cents: int) -> str:
    dollars = cents / 100.0
    return f"${dollars:.2f}"
