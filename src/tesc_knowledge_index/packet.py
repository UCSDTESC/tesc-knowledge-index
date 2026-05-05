from __future__ import annotations

import csv
from pathlib import Path

from .report import create_advisor_report
from .search import search_files


def create_packet(query: str, out_dir: str, limit: int = 50) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    hits = search_files(query, limit=limit)

    csv_path = out / "files.csv"
    links_path = out / "links.md"
    readme_path = out / "README.md"
    summary_path = out / "summary.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "score",
                "name",
                "mime_type",
                "modified_time",
                "owners",
                "source_accounts",
                "extraction_status",
                "web_view_link",
            ],
        )
        writer.writeheader()

        for hit in hits:
            writer.writerow(
                {
                    "score": hit.get("score", ""),
                    "name": hit.get("name", ""),
                    "mime_type": hit.get("mime_type", ""),
                    "modified_time": hit.get("modified_time", ""),
                    "owners": hit.get("owners", ""),
                    "source_accounts": hit.get("source_accounts", ""),
                    "extraction_status": hit.get("extraction_status", ""),
                    "web_view_link": hit.get("web_view_link", ""),
                }
            )

    with links_path.open("w", encoding="utf-8") as f:
        f.write(f"# Links for {query}\n\n")
        f.write(f"Found {len(hits)} local-index results.\n\n")

        for i, hit in enumerate(hits, start=1):
            f.write(f"{i}. [{hit.get('name', '')}]({hit.get('web_view_link', '')})\n")
            f.write(f"   - Score: {hit.get('score', '')}\n")
            f.write(f"   - Type: `{hit.get('mime_type', '')}`\n")
            f.write(f"   - Modified: {hit.get('modified_time', '')}\n")
            f.write(f"   - Found via: {hit.get('source_accounts', '')}\n")
            if hit.get("extraction_status"):
                f.write(f"   - Text extraction: {hit.get('extraction_status')}\n")
            f.write("\n")

    with readme_path.open("w", encoding="utf-8") as f:
        f.write(f"# TESC Knowledge Packet: {query}\n\n")
        f.write("Generated from the local TESC Drive knowledge index.\n\n")
        f.write("## Contents\n\n")
        f.write("- `summary.md`: advisor-ready summary and review guide\n")
        f.write("- `files.csv`: spreadsheet-style list of relevant files\n")
        f.write("- `links.md`: clickable Drive links\n\n")

        f.write("## Most Relevant Files\n\n")
        for i, hit in enumerate(hits[:10], start=1):
            f.write(f"{i}. [{hit.get('name', '')}]({hit.get('web_view_link', '')})\n")

        f.write("\n## Recommended Next Step\n\n")
        f.write(
            "Open `summary.md`, review the top 10–15 files, and then send a curated version to the advisor or board.\n"
        )

    create_advisor_report(query=query, out=str(summary_path), limit=limit)

    return out
