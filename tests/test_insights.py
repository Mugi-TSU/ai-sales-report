from types import SimpleNamespace

import pytest

from sales_report.aggregate import summarize
from sales_report.insights import (
    ClaudeInsightWriter,
    InsightError,
    RuleBasedInsightWriter,
)
from sales_report.models import Insight

INSIGHT = Insight(headline="9月は前月比+75%", findings=["a", "b"], actions=["c"])


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def make_client(response):
    return SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(response)))


def test_claude_writer_returns_parsed_insight(small_sales):
    client = make_client(SimpleNamespace(stop_reason="end_turn", parsed_output=INSIGHT))

    assert ClaudeInsightWriter(client).write(summarize(small_sales)) == INSIGHT


def test_claude_writer_sends_aggregated_numbers_only(small_sales):
    client = make_client(SimpleNamespace(stop_reason="end_turn", parsed_output=INSIGHT))

    ClaudeInsightWriter(client).write(summarize(small_sales))

    call = client.beta.messages.calls[0]
    content = call["messages"][0]["content"]
    assert '"2026-09": 7000' in content
    assert call["output_format"] is Insight


@pytest.mark.parametrize(
    ("stop_reason", "message"), [("refusal", "拒否"), ("max_tokens", "max_tokens")]
)
def test_claude_writer_raises_when_no_output(small_sales, stop_reason, message):
    client = make_client(SimpleNamespace(stop_reason=stop_reason, parsed_output=None))

    with pytest.raises(InsightError, match=message):
        ClaudeInsightWriter(client).write(summarize(small_sales))


def test_rule_based_writer_mentions_growth_and_decline(small_sales):
    insight = RuleBasedInsightWriter().write(summarize(small_sales))

    assert "+75.0%" in insight.headline
    assert any("渋谷店" in f for f in insight.findings)
    assert any("横浜店" in f for f in insight.findings)
    assert insight.actions


def test_rule_based_writer_handles_single_month():
    from tests.conftest import sale

    insight = RuleBasedInsightWriter().write(
        summarize([sale("2026-09-01", "渋谷店", "豆", 1000)])
    )

    assert "2026-09" in insight.headline
