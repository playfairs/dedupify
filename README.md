# Dedupify

A modern Spotify playlist deduplication tool that removes duplicate tracks using exact, normalized, and fuzzy matching algorithms.

## Installation

### Prerequisites

- Python 3.10 or higher
- Spotify Developer account

### Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package and project manager, written in Rust.

1. Clone the repository:
```bash
git clone https://github.com/playfairs/dedupify.git
cd dedupify
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

on Windows:
```powershell  
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Install dependencies with uv:
```bash
uv sync
```

4. Run the CLI with uv:
```bash
uv run dedupify --help
```

### Setup with pip (Traditional)

1. Clone the repository:
```bash
git clone https://github.com/playfairs/dedupify.git
cd dedupify
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in editable mode:
```bash
pip install -e .
```

### Spotify Application Setup

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Set the redirect URI to: `http://localhost:8888/callback`
4. Copy your Client ID and Client Secret

4. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

5. Edit `.env` with your credentials:
```env
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URL=http://localhost:8888/callback
```

## Usage

### CLI Commands

The tool provides three main commands:

#### Purge Duplicates

Remove duplicate tracks from a playlist:

### Running with uv

```bash
uv run dedupify purge <playlist_url_or_id>
uv run dedupify analyze <playlist_url_or_id>
uv run dedupify report <playlist_url_or_id>
```

### Running with pip (after `pip install -e .`)

```bash
dedupify purge <playlist_url_or_id>
dedupify analyze <playlist_url_or_id>
dedupify report <playlist_url_or_id>
```

Options:
- `--fuzzy`: Enable fuzzy matching
- `--fuzzy-threshold`: Set fuzzy match threshold (0-100, default: 85)
- `--backup/--no-backup`: Create backup before purging (default: enabled)
- `--dry-run`: Show changes without applying them
- `--verbose, -v`: Enable verbose logging

Examples:
```bash
dedupify purge 37i9dQZF1DXcBWIGoYBM5M

dedupify purge 37i9dQZF1DXcBWIGoYBM5M --fuzzy

dedupify purge 37i9dQZF1DXcBWIGoYBM5M --dry-run

dedupify purge 37i9dQZF1DXcBWIGoYBM5M --fuzzy --fuzzy-threshold 90
```

#### Analyze Playlist

Analyze a playlist for duplicates without modifying it:

```bash
dedupify analyze <playlist_url_or_id>
```

Options:
- `--fuzzy`: Enable fuzzy matching
- `--fuzzy-threshold`: Set fuzzy match threshold
- `--verbose, -v`: Enable verbose logging

Example:
```bash
dedupify analyze 37i9dQZF1DXcBWIGoYBM5M --fuzzy
```

#### Generate Report

Generate a detailed duplicate report:

```bash
dedupify report <playlist_url_or_id>
```

Options:
- `--fuzzy`: Enable fuzzy matching
- `--fuzzy-threshold`: Set fuzzy match threshold
- `--output, -o`: Output file (default: stdout)
- `--verbose, -v`: Enable verbose logging

Examples:
```bash
dedupify report 37i9dQZF1DXcBWIGoYBM5M

dedupify report 37i9dQZF1DXcBWIGoYBM5M -o duplicates.txt
```

### Finding Your Playlist ID

You can use either the full Spotify URL or just the playlist ID:

**Full URL:**
```
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123
```

**Playlist ID only:**
```
37i9dQZF1DXcBWIGoYBM5M
```

## Development

### Running Tests

### Running with uv

```bash
uv run pytest
```

### Running with pip

```bash
pytest
```

### Code Formatting

### Running with uv

```bash
uv run black src/ tests/
uv run ruff check src/ tests/
```

### Running with pip

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

### Running with uv

```bash
uv run mypy src/
```

### Running with pip

```bash
mypy src/
```

## How It Works

1. **Exact Matching**: Identifies duplicates by Spotify track ID (100% accurate)
2. **Normalized Matching**: Compares track names after removing common suffixes like "- Remastered", "(feat. ...)", etc.
3. **Fuzzy Matching**: Uses RapidFuzz to find similar tracks with configurable similarity threshold

The tool applies matching strategies in order: exact → normalized → fuzzy. Each strategy only processes tracks not already identified as duplicates by previous strategies.