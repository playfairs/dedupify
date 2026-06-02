import logging
import sys

import typer
from rich.console import Console
from rich.logging import RichHandler

from src.base.auth import get_spotify_client
from src.base.config import Config
from src.base.dedupe import DuplicateDetector, generate_duplicate_report
from src.base.playlist import create_backup_playlist, fetch_playlist, replace_playlist_tracks
from src.base.utils import extract_playlist_id

app = typer.Typer(help="Spotify playlist deduplication tool")
console = Console()


def setup_logging(verbose: bool = False) -> None:
    """
    Args:
        verbose: Enable verbose logging.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@app.command()
def purge(
    playlist: str = typer.Argument(..., help="Spotify playlist URL or ID"),
    fuzzy: bool = typer.Option(False, "--fuzzy", help="Enable fuzzy matching"),
    fuzzy_threshold: int = typer.Option(85, "--fuzzy-threshold", help="Fuzzy match threshold (0-100)"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup before purging"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    setup_logging(verbose)

    playlist_id = extract_playlist_id(playlist)
    if not playlist_id:
        console.print("[red]Invalid playlist URL or ID[/red]")
        raise typer.Exit(1)

    try:
        config = Config.with_options(fuzzy_threshold=fuzzy_threshold, log_level="DEBUG" if verbose else "INFO")
        sp = get_spotify_client(config)

        console.print(f"[cyan]Fetching playlist...[/cyan]")
        playlist_obj = fetch_playlist(sp, playlist_id)

        console.print(f"[cyan]Analyzing {len(playlist_obj.tracks)} tracks for duplicates...[/cyan]")
        detector = DuplicateDetector(config)
        unique_tracks, duplicate_groups = detector.find_duplicates(
            playlist_obj.tracks, use_fuzzy=fuzzy
        )

        console.print(f"\n[green]Statistics:[/green]")
        console.print(str(detector.stats))

        if not duplicate_groups:
            console.print("\n[yellow]No duplicates found![/yellow]")
            return

        if dry_run:
            console.print("\n[yellow]Dry run mode - no changes will be made[/yellow]")
            console.print(f"Would remove {detector.stats.duplicates_removed} duplicate tracks")
            console.print(f"Would keep {len(unique_tracks)} unique tracks")
            return

        if backup:
            console.print(f"\n[cyan]Creating backup...[/cyan]")
            backup_playlist = create_backup_playlist(sp, playlist_obj)
            if backup_playlist:
                console.print(f"[green]Backup created: {backup_playlist.url}[/green]")
            else:
                console.print("[yellow]Warning: Failed to create backup[/yellow]")
                if not typer.confirm("Continue without backup?"):
                    raise typer.Exit(1)

        console.print(f"\n[cyan]Purging duplicates...[/cyan]")
        replace_playlist_tracks(sp, playlist_id, unique_tracks)

        console.print(f"\n[green]Successfully purged {detector.stats.duplicates_removed} duplicates![/green]")
        console.print(f"Playlist now contains {len(unique_tracks)} unique tracks")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze(
    playlist: str = typer.Argument(..., help="Spotify playlist URL or ID"),
    fuzzy: bool = typer.Option(False, "--fuzzy", help="Enable fuzzy matching"),
    fuzzy_threshold: int = typer.Option(85, "--fuzzy-threshold", help="Fuzzy match threshold (0-100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    setup_logging(verbose)

    playlist_id = extract_playlist_id(playlist)
    if not playlist_id:
        console.print("[red]Invalid playlist URL or ID[/red]")
        raise typer.Exit(1)

    try:
        config = Config.with_options(fuzzy_threshold=fuzzy_threshold, log_level="DEBUG" if verbose else "INFO")
        sp = get_spotify_client(config)

        console.print(f"[cyan]Fetching playlist...[/cyan]")
        playlist_obj = fetch_playlist(sp, playlist_id)

        console.print(f"[cyan]Analyzing {len(playlist_obj.tracks)} tracks for duplicates...[/cyan]")
        detector = DuplicateDetector(config)
        unique_tracks, duplicate_groups = detector.find_duplicates(
            playlist_obj.tracks, use_fuzzy=fuzzy
        )

        console.print(f"\n[green]Statistics:[/green]")
        console.print(str(detector.stats))

        if duplicate_groups:
            console.print(f"\n[cyan]Found {len(duplicate_groups)} duplicate groups[/cyan]")
        else:
            console.print("\n[yellow]No duplicates found![/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def report(
    playlist: str = typer.Argument(..., help="Spotify playlist URL or ID"),
    fuzzy: bool = typer.Option(False, "--fuzzy", help="Enable fuzzy matching"),
    fuzzy_threshold: int = typer.Option(85, "--fuzzy-threshold", help="Fuzzy match threshold (0-100)"),
    output: str = typer.Option("-", "--output", "-o", help="Output file (default: stdout)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    setup_logging(verbose)

    playlist_id = extract_playlist_id(playlist)
    if not playlist_id:
        console.print("[red]Invalid playlist URL or ID[/red]")
        raise typer.Exit(1)

    try:
        config = Config.with_options(fuzzy_threshold=fuzzy_threshold, log_level="DEBUG" if verbose else "INFO")
        sp = get_spotify_client(config)

        console.print(f"[cyan]Fetching playlist...[/cyan]")
        playlist_obj = fetch_playlist(sp, playlist_id)

        console.print(f"[cyan]Analyzing {len(playlist_obj.tracks)} tracks for duplicates...[/cyan]")
        detector = DuplicateDetector(config)
        unique_tracks, duplicate_groups = detector.find_duplicates(
            playlist_obj.tracks, use_fuzzy=fuzzy
        )

        report = generate_duplicate_report(duplicate_groups)

        if output == "-":
            console.print("\n" + report)
        else:
            with open(output, "w") as f:
                f.write(report)
            console.print(f"[green]Report written to {output}[/green]")

        console.print(f"\n[green]Statistics:[/green]")
        console.print(str(detector.stats))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def cli() -> None:
    app()

if __name__ == "__main__":
    cli()
