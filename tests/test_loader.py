from datetime import date
from pathlib import Path

import pytest

from sales_report.loader import InputError, read_sales

HEADER = "date,store,category,product,quantity,unit_price\n"


def test_reads_sample_csv(sample_csv: Path):
    sales = read_sales(sample_csv)

    assert len(sales) == 633
    assert sales[0].date == date(2026, 7, 1)
    assert sales[0].amount == sales[0].quantity * sales[0].unit_price


def test_raises_for_missing_file(tmp_path: Path):
    with pytest.raises(InputError, match="見つかりません"):
        read_sales(tmp_path / "none.csv")


def test_raises_for_missing_column(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_text("date,store\n2026-07-01,渋谷店\n", encoding="utf-8")

    with pytest.raises(InputError, match="quantity"):
        read_sales(path)


@pytest.mark.parametrize(
    "row",
    [
        "2026-13-01,渋谷店,豆,深煎り,1,1000",  # 存在しない日付
        "2026-07-01,渋谷店,豆,深煎り,-1,1000",  # 負の数量
        "2026-07-01,渋谷店,豆,深煎り,abc,1000",  # 数値でない
    ],
)
def test_reports_line_number_for_invalid_row(tmp_path: Path, row: str):
    path = tmp_path / "bad.csv"
    path.write_text(HEADER + row + "\n", encoding="utf-8")

    with pytest.raises(InputError, match="2行目"):
        read_sales(path)


def test_raises_when_no_rows(tmp_path: Path):
    path = tmp_path / "empty.csv"
    path.write_text(HEADER, encoding="utf-8")

    with pytest.raises(InputError, match="データがありません"):
        read_sales(path)
