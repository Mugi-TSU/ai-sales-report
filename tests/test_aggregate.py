import pytest

from sales_report.aggregate import summarize


def test_monthly_totals(small_sales):
    summary = summarize(small_sales)

    assert summary.months == ["2026-08", "2026-09"]
    assert summary.monthly_total == {"2026-08": 4000, "2026-09": 7000}


def test_latest_month_and_change(small_sales):
    summary = summarize(small_sales)

    assert summary.latest_month == "2026-09"
    assert summary.previous_month == "2026-08"
    assert summary.mom_change_pct == pytest.approx(75.0)


def test_breakdown_by_store_fills_missing_months_with_zero(small_sales):
    summary = summarize(small_sales)

    assert summary.by_store == {
        "渋谷店": {"2026-08": 1000, "2026-09": 6000},
        "横浜店": {"2026-08": 3000, "2026-09": 1000},
    }
    assert summary.by_category["ギフト"] == {"2026-08": 0, "2026-09": 4000}


def test_top_products_in_latest_month(small_sales):
    summary = summarize(small_sales)

    assert summary.top_products[0] == ("ギフトS", 4000)
    assert [name for name, _ in summary.top_products] == [
        "ギフトS",
        "深煎り",
        "エチオピア",
    ]


def test_single_month_has_no_change():
    from tests.conftest import sale

    summary = summarize([sale("2026-09-01", "渋谷店", "豆", 1000)])

    assert summary.previous_month is None
    assert summary.mom_change_pct is None


def test_sample_data_reflects_designed_trends(sample_csv):
    from sales_report.loader import read_sales

    summary = summarize(read_sales(sample_csv))

    yokohama = summary.by_store["横浜店"]
    online = summary.by_store["オンライン"]
    assert yokohama["2026-09"] < yokohama["2026-08"]
    assert online["2026-09"] > online["2026-08"]
