#!/usr/bin/env python3
"""Delete one report by date and rebuild the archive index."""

from __future__ import annotations

import argparse
import json

from generate_report import INDEX, REPORTS, REPORTS_JSON, render_index, reports_list


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-id", required=True, help="Report date/id, for example 2026-07-05")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_id = args.report_id.strip()
    report_file = REPORTS / f"{report_id}.html"
    if report_file.exists():
        report_file.unlink()

    reports = [item for item in reports_list() if item.get("id") != report_id]
    reports.sort(key=lambda item: item["date"], reverse=True)
    REPORTS_JSON.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    INDEX.write_text(render_index(reports), encoding="utf-8")
    print(f"deleted report {report_id}")


if __name__ == "__main__":
    main()
