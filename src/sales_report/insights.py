"""集計結果から所見を書く。Claude 版と、APIキーなしで動くルールベース版がある。"""

from typing import Any, Protocol

from sales_report.aggregate import _change_pct
from sales_report.models import Insight, SalesSummary

DEFAULT_MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """\
あなたは小売店の売上分析を担当するアナリストです。
渡された集計結果（JSON）を読み、経営者向けに所見と打ち手をまとめてください。

- 数字は渡された集計結果にあるものだけを使い、推測で数字を作らないでください。
- 増減を述べるときは、どの店舗・カテゴリの、いつと比べた話かを明記してください。
- 打ち手は、店舗スタッフが来月すぐに実行できる具体的な内容にしてください。
"""


class InsightError(Exception):
    """所見を作成できなかったときに送出する。"""


class InsightWriter(Protocol):
    def write(self, summary: SalesSummary) -> Insight: ...


class ClaudeInsightWriter:
    def __init__(self, client: Any, model: str = DEFAULT_MODEL) -> None:
        self._client = client
        self._model = model

    def write(self, summary: SalesSummary) -> Insight:
        response = self._client.beta.messages.parse(
            model=self._model,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": summary.model_dump_json(indent=2)}],
            output_format=Insight,
            output_config={"effort": "medium"},
            # 安全フィルタで拒否されたとき、サーバー側で別モデルに切り替えて再実行する
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise InsightError("AIに処理を拒否されました")
        if response.parsed_output is None:
            raise InsightError(
                f"AIの応答を解析できませんでした（{response.stop_reason}）"
            )
        return response.parsed_output


class RuleBasedInsightWriter:
    """APIキーなしでデモを動かすための、決まった型の簡易コメント。"""

    def write(self, summary: SalesSummary) -> Insight:
        latest = summary.latest_month
        total = summary.monthly_total[latest]
        if summary.mom_change_pct is None:
            return Insight(
                headline=f"{latest}の売上は{total:,}円", findings=[], actions=[]
            )

        changes = _store_changes(summary)
        best, worst = changes[0], changes[-1]
        return Insight(
            headline=f"{latest}の売上は{total:,}円（前月比{summary.mom_change_pct:+.1f}%）",
            findings=[
                f"{best[0]}が前月比{best[1]:+.1f}%と最も伸びています",
                f"{worst[0]}は前月比{worst[1]:+.1f}%と最も落ち込んでいます",
                f"売上1位の商品は「{summary.top_products[0][0]}」です",
            ],
            actions=[
                f"{worst[0]}の落ち込みの原因（客数・客単価）を確認する",
                f"{best[0]}で売れている商品を他店舗でも展開する",
            ],
        )


def _store_changes(summary: SalesSummary) -> list[tuple[str, float]]:
    prev, latest = summary.previous_month, summary.latest_month
    changes = [
        (store, pct)
        for store, amounts in summary.by_store.items()
        if (pct := _change_pct(amounts[prev], amounts[latest])) is not None
    ]
    return sorted(changes, key=lambda c: c[1], reverse=True)
