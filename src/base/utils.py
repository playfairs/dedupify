import re
import unicodedata
from typing import Optional


def extract_playlist_id(url: str) -> Optional[str]:
    """
    Args:
        url: Spotify playlist URL or ID.
    Returns:
        Playlist ID if found, None otherwise.
    """
    if re.match(r'^[a-zA-Z0-9]{22}$', url):
        return url

    match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None


def normalize_string(text: str) -> str:
    """
    Args:
        text: String to normalize.
    Returns:
        Normalized string.
    """
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = ' '.join(text.split()).lower()
    return text


def normalize_track_name(name: str) -> str:
    """
    Args:
        name: Track name to normalize.
    Returns:
        Normalized track name.
    """
    name = normalize_string(name)
    suffixes = [
        r'\s*-\s*remastered',
        r'\s*-\s*remaster',
        r'\s*-\s*deluxe',
        r'\s*-\s*explicit',
        r'\s*-\s*clean',
        r'\s*-\s*radio edit',
        r'\s*-\s*album version',
        r'\s*\(feat\.[^\)]*\)',
        r'\s*\(ft\.[^\)]*\)',
        r'\s*\[feat\.[^\]]*\]',
        r'\s*\[ft\.[^\]]*\]',
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
    return name.strip()


def create_track_key(track_name: str, artist_name: str) -> str:
    """
    Args:
        track_name: Name of the track.
        artist_name: Name of the primary artist.
    Returns:
        Normalized track key.
    """
    normalized_name = normalize_track_name(track_name)
    normalized_artist = normalize_string(artist_name)
    return f"{normalized_name} - {normalized_artist}"
