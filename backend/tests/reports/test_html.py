from __future__ import annotations

from html.parser import HTMLParser

from app import __version__
from app.debate.models import DebateReport
from app.reports.html import render_html


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        self.tags.append(tag)

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text.append(" ".join(data.split()))


def parse(html: str) -> _Collector:
    collector = _Collector()
    collector.feed(html)
    return collector


def test_demo_report_is_one_self_contained_page(demo_report: DebateReport) -> None:
    html = render_html(demo_report)
    page = parse(html)

    assert html.startswith("<!doctype html>")
    assert "<script" not in html and "<link" not in html  # no external resources
    assert page.tags.count("h2") == 6
    assert "190,799.27" in page.text and "218,696.07" in page.text
    assert "+14.62%" in page.text and "82%" in page.text
    assert f'content="CostCourt {__version__}"' in html


def test_user_text_is_escaped(report: DebateReport) -> None:
    html = render_html(report)
    page = parse(html)

    assert "<script>alert(1)</script>" not in html
    assert "<title>CostCourt report: Garage &lt;script&gt;alert(1)&lt;/script&gt;</title>" in html
    assert "Concrete &lt;b&gt;C30&lt;/b&gt; | slab" in html
    assert "Formwork is &lt;em&gt;not&lt;/em&gt; needed." in html
    assert "script" not in page.tags and "b" not in page.tags and "em" not in page.tags


def test_rulings_and_line_changes(report: DebateReport) -> None:
    html = render_html(report)
    text = " ".join(parse(html).text)

    assert "Adjusted" in text and "Removed" in text
    assert "Removed: 50 m² at 20.00" in text
    assert "Proposes quantity 12 and unit rate 110.00 · Answers the estimator" in text
    assert '<tr class="removed">' in html
    assert '<tr class="changed">' in html
    assert "Winter blankets are not priced." in text
