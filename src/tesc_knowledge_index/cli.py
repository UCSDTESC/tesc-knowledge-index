from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .auth import CREDENTIALS_PATH, TOKENS_DIR, get_credentials
from .crawler import crawl_account, drive_search_account
from .database import connect, init_db, rebuild_all_fts, upsert_file
from .extractors import extract_for_query, extract_pending
from .packet import create_packet
from .report import create_advisor_report
from .search import search_files


app = typer.Typer(help="TESC Google Drive knowledge indexer.")
auth_app = typer.Typer(help="Manage Google account authentication.")
app.add_typer(auth_app, name="auth")

console = Console()


@auth_app.command("add")
def auth_add(
    account: str = typer.Option(..., help="Account label, e.g. rohan or contact"),
):
    get_credentials(account)
    console.print(f"[green]Authenticated account label:[/green] {account}")


@app.command()
def init():
    init_db()
    console.print("[green]Initialized local SQLite index.[/green]")


@app.command()
def doctor():
    console.print("[bold]TESC Knowledge Index Doctor[/bold]\n")

    checks = [
        ("credentials/client_secret.json", CREDENTIALS_PATH.exists()),
        ("tokens directory", TOKENS_DIR.exists()),
        ("data directory", Path("data").exists()),
        ("exports directory", Path("exports").exists()),
        ("SQLite database", Path("data/index.sqlite").exists()),
    ]

    for name, ok in checks:
        status = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        console.print(f"{status} {name}")

    console.print("\nRun `tesc-drive stats` to inspect indexed files.")


@app.command("rebuild-fts")
def rebuild_fts():
    init_db()
    with connect() as conn:
        count = rebuild_all_fts(conn)
    console.print(f"[green]Rebuilt local search index for {count} files.[/green]")


@app.command()
def stats():
    init_db()

    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM files").fetchone()["n"]

        text_total = conn.execute("SELECT COUNT(*) AS n FROM file_text").fetchone()["n"]

        text_ok = conn.execute(
            "SELECT COUNT(*) AS n FROM file_text WHERE extraction_status = 'ok'"
        ).fetchone()["n"]

        by_account = conn.execute(
            """
            SELECT source_accounts, COUNT(*) AS n
            FROM files
            GROUP BY source_accounts
            ORDER BY n DESC
            """
        ).fetchall()

        by_type = conn.execute(
            """
            SELECT mime_type, COUNT(*) AS n
            FROM files
            GROUP BY mime_type
            ORDER BY n DESC
            LIMIT 20
            """
        ).fetchall()

    console.print(f"[green]Total unique files indexed:[/green] {total}")
    console.print(f"[green]Files with extraction records:[/green] {text_total}")
    console.print(f"[green]Files with successful text extraction:[/green] {text_ok}")

    account_table = Table(title="Files by source account")
    account_table.add_column("Source accounts")
    account_table.add_column("Count", justify="right")

    for row in by_account:
        account_table.add_row(row["source_accounts"] or "", str(row["n"]))

    console.print(account_table)

    type_table = Table(title="Top MIME types")
    type_table.add_column("MIME type")
    type_table.add_column("Count", justify="right")

    for row in by_type:
        type_table.add_row(row["mime_type"] or "", str(row["n"]))

    console.print(type_table)


@app.command()
def index(
    account: str = typer.Option(..., help="Account label previously authenticated."),
    max_pages: int | None = typer.Option(None, help="Limit pages for testing."),
):
    init_db()
    count = crawl_account(account=account, max_pages=max_pages)
    console.print(f"[green]Done. Indexed {count} files for {account}.[/green]")


@app.command()
def search(
    query: str,
    limit: int = typer.Option(25, help="Maximum results."),
    links: bool = typer.Option(
        False, help="Show full raw links instead of compact table."
    ),
    preview: bool = typer.Option(
        False, help="Show extracted text preview when available."
    ),
):
    init_db()
    hits = search_files(query, limit=limit)

    if links:
        console.print(f"\n[bold]Search results for:[/bold] {query}\n")
        for i, hit in enumerate(hits, start=1):
            console.print(f"[bold]{i}. {hit.get('name', '')}[/bold]")
            console.print(f"   Score: {hit.get('score', '')}")
            console.print(f"   Type: {hit.get('mime_type', '')}")
            console.print(f"   Modified: {hit.get('modified_time', '')}")
            console.print(f"   Found via: {hit.get('source_accounts', '')}")
            console.print(f"   Text extraction: {hit.get('extraction_status', '')}")
            console.print(f"   Link: {hit.get('web_view_link', '')}")
            if preview and hit.get("text_preview"):
                console.print(f"   Preview: {hit.get('text_preview', '')[:300]}")
            console.print()
        return

    table = Table(title=f"Search results for: {query}", show_lines=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Name", overflow="fold", ratio=3)
    table.add_column("Type", overflow="fold", ratio=2)
    table.add_column("Modified", width=20)
    table.add_column("Found Via", width=16)
    table.add_column("Text", width=8)
    table.add_column("Open", width=8)

    for i, hit in enumerate(hits, start=1):
        link = hit.get("web_view_link", "")
        open_text = f"[link={link}]Open[/link]" if link else ""
        text_status = hit.get("extraction_status", "")

        table.add_row(
            str(i),
            str(hit.get("score", "")),
            hit.get("name", ""),
            hit.get("mime_type", ""),
            hit.get("modified_time", ""),
            hit.get("source_accounts", ""),
            text_status,
            open_text,
        )

    console.print(table)


@app.command("drive-search")
def drive_search(
    query: str,
    account: str = typer.Option(..., help="Account label previously authenticated."),
    limit: int = typer.Option(25, help="Maximum results."),
    links: bool = typer.Option(
        False, help="Show full raw links instead of compact table."
    ),
):
    init_db()
    hits = drive_search_account(account=account, query=query, limit=limit)

    # Important: live Drive search now strengthens local DB.
    for hit in hits:
        upsert_file(hit, account)

    if links:
        console.print(
            f"\n[bold]Live Google Drive search for:[/bold] {query} via {account}\n"
        )
        for i, hit in enumerate(hits, start=1):
            console.print(f"[bold]{i}. {hit.get('name', '')}[/bold]")
            console.print(f"   Type: {hit.get('mimeType', '')}")
            console.print(f"   Modified: {hit.get('modifiedTime', '')}")
            console.print(f"   Link: {hit.get('webViewLink', '')}\n")
        return

    table = Table(
        title=f"Live Google Drive search for: {query} via {account}", show_lines=True
    )
    table.add_column("#", justify="right", width=4)
    table.add_column("Name", overflow="fold", ratio=3)
    table.add_column("Type", overflow="fold", ratio=2)
    table.add_column("Modified", width=20)
    table.add_column("Open", width=8)

    for i, hit in enumerate(hits, start=1):
        link = hit.get("webViewLink", "")
        open_text = f"[link={link}]Open[/link]" if link else ""

        table.add_row(
            str(i),
            hit.get("name", ""),
            hit.get("mimeType", ""),
            hit.get("modifiedTime", ""),
            open_text,
        )

    console.print(table)
    console.print("[green]Saved live Drive results into local index.[/green]")


@app.command()
def links(
    query: str,
    limit: int = typer.Option(25, help="Maximum results."),
):
    init_db()
    hits = search_files(query, limit=limit)

    for i, hit in enumerate(hits, start=1):
        console.print(f"{i}. {hit.get('name', '')}")
        console.print(f"   {hit.get('web_view_link', '')}")
        console.print(
            f"   Score: {hit.get('score', '')} | "
            f"Modified: {hit.get('modified_time', '')} | "
            f"Found via: {hit.get('source_accounts', '')} | "
            f"Text: {hit.get('extraction_status', '')}"
        )
        console.print()


@app.command("export-links")
def export_links(
    query: str,
    out: str = typer.Option(..., help="Output Markdown file."),
    limit: int = typer.Option(50, help="Maximum results."),
):
    init_db()
    hits = search_files(query, limit=limit)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"# TESC Drive Links: {query}\n\n")
        f.write(f"Found {len(hits)} local-index results.\n\n")

        for i, hit in enumerate(hits, start=1):
            f.write(f"## {i}. {hit.get('name', '')}\n\n")
            f.write(f"- Score: {hit.get('score', '')}\n")
            f.write(f"- Link: {hit.get('web_view_link', '')}\n")
            f.write(f"- Type: `{hit.get('mime_type', '')}`\n")
            f.write(f"- Modified: {hit.get('modified_time', '')}\n")
            f.write(f"- Found via: {hit.get('source_accounts', '')}\n")
            f.write(f"- Owners: {hit.get('owners', '')}\n")
            f.write(f"- Text extraction: {hit.get('extraction_status', '')}\n\n")

    console.print(f"[green]Exported links to:[/green] {out_path}")


@app.command()
def extract(
    account: str = typer.Option(..., help="Account label to use for extraction."),
    query: str | None = typer.Option(
        None, help="Only extract top local search results for this query."
    ),
    limit: int = typer.Option(100, help="Maximum files to extract this run."),
    force: bool = typer.Option(
        False, help="Re-extract files even if already extracted."
    ),
):
    init_db()

    if query:
        success, failed, skipped = extract_for_query(
            account=account,
            query=query,
            limit=limit,
            force=force,
        )
    else:
        console.print(
            "[yellow]No query provided, so this will extract arbitrary pending files from the whole database.[/yellow]"
        )
        console.print(
            '[yellow]For normal use, prefer: tesc-drive extract --account contact --query "SD Hacks" --limit 50[/yellow]'
        )
        success, failed, skipped = extract_pending(
            account=account,
            limit=limit,
            force=force,
        )

    console.print("[green]Text extraction complete.[/green]")
    console.print(f"Successful: {success}")
    console.print(f"Empty/failed: {failed}")
    console.print(f"Skipped: {skipped}")


@app.command()
def report(
    query: str,
    out: str = typer.Option(..., help="Output Markdown report file."),
    limit: int = typer.Option(75, help="Maximum files to include."),
):
    init_db()
    path = create_advisor_report(query=query, out=out, limit=limit)
    console.print(f"[green]Created advisor-ready report:[/green] {path}")


@app.command()
def packet(
    query: str,
    out: str = typer.Option(..., help="Output directory."),
    limit: int = typer.Option(75, help="Maximum files in packet."),
):
    init_db()
    path = create_packet(query=query, out_dir=out, limit=limit)
    console.print(f"[green]Created packet:[/green] {path}")
