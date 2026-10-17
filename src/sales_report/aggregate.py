"""売上を月別・店舗別・カテゴリ別に集計する。"""

from collections import defaultdict
from collections.abc import Callable

from sales_report.models import MonthlyAmounts, Sale, SalesSummary

TOP_PRODUCT_COUNT = 5


def summarize(sales: list[Sale]) -> SalesSummary:
    months = sorted({_month(s) for s in sales})
    latest = months[-1]
    previous = months[-2] if len(months) >= 2 else None
    monthly_total = _sum_by_month(sales, months)

    return SalesSummary(
        months=months,
        monthly_total=monthly_total,
        by_store=_breakdown(sales, months, key=lambda s: s.store),
        by_category=_breakdown(sales, months, key=lambda s: s.category),
        top_products=_top_products([s for s in sales if _month(s) == latest]),
        latest_month=latest,
        previous_month=previous,
        mom_change_pct=_change_pct(monthly_total[previous], monthly_total[latest])
        if previous
        else None,
    )


def _month(sale: Sale) -> str:
    return sale.date.strftime("%Y-%m")


def _sum_by_month(sales: list[Sale], months: list[str]) -> MonthlyAmounts:
    totals = dict.fromkeys(months, 0)
    for s in sales:
        totals[_month(s)] += s.amount
    return totals


def _breakdown(
    sales: list[Sale], months: list[str], key: Callable[[Sale], str]
) -> dict[str, MonthlyAmounts]:
    groups: dict[str, list[Sale]] = defaultdict(list)
    for s in sales:
        groups[key(s)].append(s)
    # 初出順を保ち、売上のない月は 0 で埋める
    return {name: _sum_by_month(items, months) for name, items in groups.items()}


def _top_products(sales: list[Sale]) -> list[tuple[str, int]]:
    totals: dict[str, int] = defaultdict(int)
    for s in sales:
        totals[s.product] += s.amount
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:TOP_PRODUCT_COUNT]


def _change_pct(before: int, after: int) -> float | None:
    if before == 0:
        return None
    return round((after - before) / before * 100, 1)
