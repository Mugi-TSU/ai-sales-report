"""コマンドラインの入口。"""

import argparse
import os
import sys
from pathlib import Path

import anthropic

from sales_report.aggregate import summarize
from sales_report.insights import (
    DEFAULT_MODEL,
    ClaudeInsightWriter,
    InsightError,
    InsightWriter,
    RuleBasedInsightWriter,
)
from sales_report.loader import InputError, read_sales
from sales_report.report import write_report


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = summarize(read_sales(args.input))
    except InputError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    if not args.mock and not _has_api_key():
        print(
            "エラー: 環境変数 ANTHROPIC_API_KEY を設定するか、--mock を付けて実行してください",
            file=sys.stderr,
        )
        return 1

    ai_generated = not args.mock
    try:
        insight = _build_writer(args).write(summary)
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
        print(f"エラー: APIキーを確認してください（{e.status_code}）", file=sys.stderr)
        return 1
    except (InsightError, anthropic.APIError) as e:
        # 集計結果は正しいので、所見だけ簡易コメントに切り替えてレポートは作る
        print(
            f"警告: AIの所見を作成できなかったため、簡易コメントで出力します（{e}）",
            file=sys.stderr,
        )
        insight = RuleBasedInsightWriter().write(summary)
        ai_generated = False

    write_report(summary, insight, args.output, ai_generated=ai_generated)
    print(
        f"{summary.latest_month}のレポートを作成しました: {insight.headline} → {args.output}"
    )
    return 0


def _has_api_key() -> bool:
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def _build_writer(args: argparse.Namespace) -> InsightWriter:
    if args.mock:
        return RuleBasedInsightWriter()
    return ClaudeInsightWriter(anthropic.Anthropic(), model=args.model)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="売上CSVを集計し、AIの所見つきExcelレポートを作成します"
    )
    parser.add_argument("input", type=Path, help="売上のCSVファイル")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("output/sales_report.xlsx")
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="使用するClaudeのモデル")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="APIを使わず簡易コメントで出力する（お試し用）",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
