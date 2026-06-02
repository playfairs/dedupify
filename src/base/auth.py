import logging

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from src.config import Config

logger = logging.getLogger(__name__)


def get_spotify_client(config: Config) -> spotipy.Spotify:
    """
    Args:
        config: Application configuration containing credentials.
    Returns:
        Authenticated Spotify client.
    Raises:
        Exception: If authentication fails.
    """
    try:
        auth_manager = SpotifyOAuth(
            scope="playlist-read-private playlist-modify-public playlist-modify-private",
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_url,
        )
        client = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("Successfully authenticated with Spotify")
        return client
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise
