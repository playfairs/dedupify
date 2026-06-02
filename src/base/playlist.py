import logging
from typing import Optional

import spotipy

from src.models import Playlist, Track

logger = logging.getLogger(__name__)


def fetch_playlist(sp: spotipy.Spotify, playlist_id: str) -> Playlist:
    """
    Args:
        sp: Authenticated Spotify client.
        playlist_id: Spotify playlist ID.
    Returns:
        Playlist object with all tracks.
    Raises:
        Exception: If playlist fetch fails.
    """
    try:
        playlist_info = sp.playlist(playlist_id)
        playlist = Playlist(
            id=playlist_id,
            name=playlist_info["name"],
            url=playlist_info["external_urls"]["spotify"],
            snapshot_id=playlist_info.get("snapshot_id"),
        )

        results = sp.playlist_items(playlist_id, additional_types=["track"])
        items = results["items"]

        while results["next"]:
            results = sp.next(results)
            items.extend(results["items"])

        logger.info(f"Fetched {len(items)} tracks from playlist '{playlist.name}'")

        for item in items:
            track = item.get("track")
            if not track:
                continue

            if "name" not in track or "artists" not in track:
                continue

            if "external_urls" not in track or "spotify" not in track["external_urls"]:
                continue

            artists = [a["name"] for a in track["artists"]]
            playlist.tracks.append(
                Track(
                    id=track["id"],
                    name=track["name"],
                    artists=artists,
                    url=track["external_urls"]["spotify"],
                    is_local=track.get("is_local", False),
                )
            )

        return playlist

    except Exception as e:
        logger.error(f"Failed to fetch playlist: {e}")
        raise


def create_backup_playlist(
    sp: spotipy.Spotify,
    playlist: Playlist,
    suffix: str = " (Backup)",
) -> Optional[Playlist]:
    """
    Args:
        sp: Authenticated Spotify client.
        playlist: Playlist to backup.
        suffix: Suffix to append to backup name.
    Returns:
        New backup playlist if successful, None otherwise.
    """
    try:
        user_id = sp.me()["id"]
        backup_name = f"{playlist.name}{suffix}"

        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=backup_name,
            public=False,
            description=f"Backup of {playlist.url}",
        )

        backup_playlist = Playlist(
            id=new_playlist["id"],
            name=new_playlist["name"],
            url=new_playlist["external_urls"]["spotify"],
        )

        track_urls = [track.url for track in playlist.tracks]
        sp.playlist_add_items(backup_playlist.id, track_urls[:100])

        for i in range(100, len(track_urls), 100):
            sp.playlist_add_items(backup_playlist.id, track_urls[i : i + 100])

        logger.info(f"Created backup playlist: {backup_playlist.url}")
        return backup_playlist

    except Exception as e:
        logger.error(f"Failed to create backup playlist: {e}")
        return None


def replace_playlist_tracks(
    sp: spotipy.Spotify,
    playlist_id: str,
    tracks: list[Track],
) -> None:
    """
    Args:
        sp: Authenticated Spotify client.
        playlist_id: Spotify playlist ID.
        tracks: List of tracks to replace with.
    Raises:
        Exception: If track replacement fails.
    """
    try:
        track_urls = [track.url for track in tracks]

        sp.playlist_replace_items(playlist_id, track_urls[:100])

        for i in range(100, len(track_urls), 100):
            sp.playlist_add_items(playlist_id, track_urls[i : i + 100])

        logger.info(f"Replaced {len(track_urls)} tracks in playlist")

    except Exception as e:
        logger.error(f"Failed to replace playlist tracks: {e}")
        raise
