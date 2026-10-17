"""売上データ・集計結果・AIの所見のデータ型。"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, computed_field

# 月 -> 金額（例: {"2026-09": 120000}）
MonthlyAmounts = dict[str, int]


class Sale(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    store: str = Field(min_length=1)
    category: str = Field(min_length=1)
    product: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)

    @computed_field
    @property
    def amount(self) -> int:
        return self.quantity * self.unit_price


class SalesSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    months: list[str]
    monthly_total: MonthlyAmounts
    by_store: dict[str, MonthlyAmounts]
    by_category: dict[str, MonthlyAmounts]
    top_products: list[tuple[str, int]]
    latest_month: str
    previous_month: str | None
    mom_change_pct: float | None


class Insight(BaseModel):
    """AIが返す所見。Claude の structured outputs のスキーマにもなる。"""

    model_config = ConfigDict(frozen=True)

    headline: str = Field(description="最新月の売上を一言で表す見出し（40字以内）")
    findings: list[str] = Field(
        description="数字に基づく気づき。3つ程度、それぞれ80字以内"
    )
    actions: list[str] = Field(
        description="来月に向けた具体的な打ち手。3つ程度、それぞれ80字以内"
    )
