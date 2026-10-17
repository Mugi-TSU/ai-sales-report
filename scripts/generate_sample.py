"""デモ用の架空の売上データを生成する（乱数シード固定で毎回同じ内容）。"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
START, END = date(2026, 7, 1), date(2026, 9, 30)
PRODUCTS = {
    "コーヒー豆": [
        ("深煎りブレンド 200g", 1480),
        ("エチオピア 200g", 1780),
        ("デカフェ 200g", 1680),
    ],
    "ドリップバッグ": [("ドリップバッグ 10個入", 1200), ("飲み比べ 5種セット", 980)],
    "器具": [("ハンドドリッパー", 2800), ("電動ミル", 8900)],
    "ギフト": [("ギフトセットS", 3500), ("ギフトセットL", 5800)],
}
# 店舗ごとの月別の客数の伸び（オンラインが成長、横浜店は9月に落ち込む）
STORE_TREND = {
    "渋谷店": {7: 1.0, 8: 1.05, 9: 1.0},
    "横浜店": {7: 0.9, 8: 0.85, 9: 0.6},
    "オンライン": {7: 0.8, 8: 1.0, 9: 1.3},
}
# 9月は敬老の日・秋の贈答でギフトの購入数が伸びる
GIFT_BOOST = {7: 1.0, 8: 0.9, 9: 1.6}
BASE_PROBABILITY = 0.6


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    day = START
    while day <= END:
        for store, trend in STORE_TREND.items():
            for category, items in PRODUCTS.items():
                # 店舗の勢いは「売れる日の多さ」、ギフト需要は「1回の購入数」に表す
                if rng.random() > BASE_PROBABILITY * trend[day.month]:
                    continue
                boost = GIFT_BOOST[day.month] if category == "ギフト" else 1.0
                name, price = rng.choice(items)
                qty = max(1, round(rng.gauss(3 * boost, 1)))
                rows.append([day.isoformat(), store, category, name, qty, price])
        day += timedelta(days=1)

    out = Path(__file__).resolve().parents[1] / "data" / "sample_sales.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["date", "store", "category", "product", "quantity", "unit_price"]
        )
        writer.writerows(rows)
    print(f"{len(rows)}行を書き出しました: {out}")


if __name__ == "__main__":
    main()
