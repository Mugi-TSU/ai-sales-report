from datetime import date
from pathlib import Path

import pytest

from sales_report.models import Sale

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"


@pytest.fixture
def sample_csv() -> Path:
    return SAMPLE_CSV


def sale(
    day: str, store: str, category: str, amount: int, product: str = "商品A"
) -> Sale:
    return Sale(
        date=date.fromisoformat(day),
        store=store,
        category=category,
        product=product,
        quantity=1,
        unit_price=amount,
    )


@pytest.fixture
def small_sales() -> list[Sale]:
    return [
        sale("2026-08-03", "渋谷店", "豆", 1000, "深煎り"),
        sale("2026-08-10", "横浜店", "豆", 3000, "深煎り"),
        sale("2026-09-05", "渋谷店", "豆", 2000, "深煎り"),
        sale("2026-09-06", "渋谷店", "ギフト", 4000, "ギフトS"),
        sale("2026-09-20", "横浜店", "豆", 1000, "エチオピア"),
    ]
