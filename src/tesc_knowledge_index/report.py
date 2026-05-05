from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from .search import search_files


def _year_from_time(value: str) -> str:
    match = re.match(r"(\d{4})-", value or "")
    return match.group(1) if match else "Unknown"


def _category_for_hit(hit: dict) -> str:
    name = (hit.get("name") or "").lower()
    mime = hit.get("mime_type") or ""

    if "sponsor" in name or "prospectus" in name or "donation" in name:
        return "Sponsorship / fundraising"
    if "budget" in name or "invoice" in name or "receipt" in name:
        return "Budget / finance"
    if (
        "logistic" in name
        or "operations" in name
        or "day-of" in name
        or "day of" in name
    ):
        return "Operations / day-of logistics"
    if "application" in name or "recruit" in name or "committee" in name:
        return "Recruiting / applications"
    if "timeline" in name or "planning" in name or "guide" in name or "master" in name:
        return "Planning / institutional memory"
    if "form" in mime or "responses" in name:
        return "Forms / responses"
    if "presentation" in mime or name.endswith(".pptx"):
        return "Slides / presentations"
    if "spreadsheet" in mime or name.endswith(".xlsx") or name.endswith(".csv"):
        return "Spreadsheets / trackers"
    if "document" in mime or name.endswith(".docx"):
        return "Docs / notes"
    if "pdf" in mime:
        return "PDFs"
    return "Other"


def _brief_inference(categories: Counter[str]) -> list[str]:
    bullets: list[str] = []

    if categories["Planning / institutional memory"]:
        bullets.append(
            "TESC appears to have maintained planning guides, master documents, or institutional-memory documents for this topic."
        )
    if categories["Operations / day-of logistics"]:
        bullets.append(
            "There are day-of logistics or operations materials, suggesting TESC had an execution/support role rather than only a promotional role."
        )
    if categories["Sponsorship / fundraising"]:
        bullets.append(
            "There are sponsorship or fundraising materials, which may be useful for understanding sponsor outreach, company packets, or donor-facing messaging."
        )
    if categories["Budget / finance"]:
        bullets.append(
            "There are budget, invoice, receipt, or finance-related records that may help reconstruct historical costs and sponsor/payment relationships."
        )
    if categories["Recruiting / applications"]:
        bullets.append(
            "There are recruiting, application, or committee materials, which may show how staffing and volunteer pipelines were handled."
        )
    if categories["Forms / responses"]:
        bullets.append(
            "There are form/response artifacts that may contain attendance, applications, judging, or feedback data."
        )

    if not bullets:
        bullets.append(
            "The current packet mainly contains general files. Review the top links manually before making strong claims about TESC’s role."
        )

    return bullets


def create_advisor_report(query: str, out: str, limit: int = 75) -> Path:
    hits = search_files(query, limit=limit)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    categories = Counter(_category_for_hit(hit) for hit in hits)
    by_year: dict[str, list[dict]] = defaultdict(list)

    for hit in hits:
        by_year[_year_from_time(hit.get("modified_time", ""))].append(hit)

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"# Advisor-Ready TESC Knowledge Summary: {query}\n\n")
        f.write(
            "This report was generated from the local TESC Google Drive knowledge index. It should be treated as a high-quality starting point, not a final historical claim, until the top linked files are manually reviewed.\n\n"
        )

        f.write("## Executive Summary\n\n")
        if hits:
            f.write(
                f"The local index found **{len(hits)} relevant files** for `{query}`. The strongest evidence appears in the top-ranked documents, folders, spreadsheets, PDFs, and presentations listed below.\n\n"
            )
        else:
            f.write(
                f"No local-index files were found for `{query}`. Try running live Drive search for both accounts, then rerun this report.\n\n"
            )

        f.write("## What TESC appears to have done\n\n")
        for bullet in _brief_inference(categories):
            f.write(f"- {bullet}\n")
        f.write("\n")

        f.write("## Most Relevant Resources\n\n")
        for i, hit in enumerate(hits[:15], start=1):
            f.write(f"{i}. [{hit.get('name', '')}]({hit.get('web_view_link', '')})\n")
            f.write(f"   - Type: `{hit.get('mime_type', '')}`\n")
            f.write(f"   - Modified: {hit.get('modified_time', '')}\n")
            f.write(f"   - Found via: {hit.get('source_accounts', '')}\n")
            if hit.get("extraction_status"):
                f.write(f"   - Text extraction: {hit.get('extraction_status')}\n")
            f.write("\n")

        f.write("## Resource Categories\n\n")
        for category, count in categories.most_common():
            f.write(f"- **{category}:** {count}\n")
        f.write("\n")

        f.write("## Timeline by Modified Year\n\n")
        for year in sorted(by_year.keys(), reverse=True):
            f.write(f"### {year}\n\n")
            for hit in by_year[year][:10]:
                f.write(f"- [{hit.get('name', '')}]({hit.get('web_view_link', '')})")
                f.write(f" — `{hit.get('mime_type', '')}`")
                if hit.get("modified_time"):
                    f.write(f" — {hit.get('modified_time')}")
                f.write("\n")
            f.write("\n")

        f.write("## Recommended Manual Review Order\n\n")
        review_order = [
            "Master documents, planning guides, and operations docs",
            "Sponsorship packets, prospectuses, invoices, and budget materials",
            "Spreadsheets containing applications, judging, responses, or trackers",
            "Slides and PDFs likely used externally",
            "Folders that may contain nested historical context",
        ]

        for item in review_order:
            f.write(f"- {item}\n")
        f.write("\n")

        f.write("## Notes and Limitations\n\n")
        f.write(
            "- This report is generated from files visible to the authenticated TESC accounts.\n"
        )
        f.write("- Some files may be duplicates, old copies, or incomplete drafts.\n")
        f.write(
            "- Google Drive live search may find files whose contents are not yet extracted locally.\n"
        )
        f.write(
            "- Review top files before sending final conclusions to an advisor or board member.\n"
        )

    return out_path
