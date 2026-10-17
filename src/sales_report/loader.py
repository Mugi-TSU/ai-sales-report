"""売上CSVを読み込む。"""

import csv
from pathlib import Path

from pydantic import ValidationError

from sales_report.models import Sale

REQUIRED_COLUMNS = ("date", "store", "category", "product", "quantity", "unit_price")


class InputError(Exception):
    """入力ファイルの形式が不正なときに送出する。"""


def read_sales(path: Path) -> list[Sale]:
    if not path.exists():
        raise InputError(f"入力ファイルが見つかりません: {path}")

    # Excel で保存した CSV の BOM を許容する
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise InputError(f"必須の列がありません: {', '.join(missing)}")
        sales = [_to_sale(row, line_no) for line_no, row in enumerate(reader, start=2)]

    if not sales:
        raise InputError("売上のデータがありません")
    return sales


def _to_sale(row: dict[str, str], line_no: int) -> Sale:
    try:
        return Sale(**{c: (row[c] or "").strip() for c in REQUIRED_COLUMNS})
    except ValidationError as e:
        error = e.errors()[0]
        raise InputError(
            f"{line_no}行目の「{error['loc'][0]}」が不正です: {error['msg']}"
        ) from e
