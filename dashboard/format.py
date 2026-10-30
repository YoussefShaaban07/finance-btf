"""Display formatting shared by every view."""


def money(x: float) -> str:
    """$1,234.56, or −$1,234.56 for negatives (a true minus sign, sign before the dollar sign)."""
    return f"\u2212${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def pretty(category: str) -> str:
    """FOOD_AND_DRINK -> Food & drink."""
    return category.replace("_", " ").lower().capitalize().replace(" and ", " & ")
