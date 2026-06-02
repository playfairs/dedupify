import logging
from typing import Optional

from rapidfuzz import fuzz, process

from src.config import Config
from src.models import DedupeStats, DuplicateGroup, Track
from src.utils import create_track_key, normalize_track_name, normalize_string

logger = logging.getLogger(__name__)


class DuplicateDetector:
    def __init__(self, config: Config):
        """
        Args:
            config: Application configuration.
        """
        self.config = config
        self.stats = DedupeStats()

    def find_duplicates(
        self,
        tracks: list[Track],
        use_fuzzy: bool = False,
    ) -> tuple[list[Track], list[DuplicateGroup]]:
        """
        Args:
            tracks: List of tracks to analyze.
            use_fuzzy: Whether to use fuzzy matching.
        Returns:
            Tuple of (unique tracks, duplicate groups).
        """
        self.stats = DedupeStats(total_tracks=len(tracks))

        unique_tracks, exact_duplicates = self._find_exact_duplicates(tracks)
        self.stats.exact_matches = sum(len(g.duplicates) for g in exact_duplicates)

        unique_tracks, normalized_duplicates = self._find_normalized_duplicates(
            unique_tracks
        )
        self.stats.normalized_matches = sum(len(g.duplicates) for g in normalized_duplicates)

        fuzzy_duplicates = []
        if use_fuzzy:
            unique_tracks, fuzzy_duplicates = self._find_fuzzy_duplicates(unique_tracks)
            self.stats.fuzzy_matches = sum(len(g.duplicates) for g in fuzzy_duplicates)

        all_duplicates = exact_duplicates + normalized_duplicates + fuzzy_duplicates
        self.stats.duplicates_removed = sum(len(g.duplicates) for g in all_duplicates)
        self.stats.unique_tracks = len(unique_tracks)

        logger.info(
            f"Found {self.stats.duplicates_removed} duplicates: "
            f"{self.stats.exact_matches} exact, "
            f"{self.stats.normalized_matches} normalized, "
            f"{self.stats.fuzzy_matches} fuzzy"
        )

        return unique_tracks, all_duplicates

    def _find_exact_duplicates(
        self, tracks: list[Track]
    ) -> tuple[list[Track], list[DuplicateGroup]]:
        """
        Args:
            tracks: List of tracks to analyze.
        Returns:
            Tuple of (unique tracks, duplicate groups).
        """
        seen_ids = {}
        duplicate_groups = []

        for track in tracks:
            if track.id in seen_ids:
                seen_ids[track.id].append(track)
            else:
                seen_ids[track.id] = [track]

        unique_tracks = []
        for track_id, track_list in seen_ids.items():
            if len(track_list) > 1:
                duplicate_groups.append(
                    DuplicateGroup(
                        canonical=track_list[0],
                        duplicates=track_list[1:],
                        match_type="exact",
                    )
                )
            unique_tracks.append(track_list[0])

        return unique_tracks, duplicate_groups

    def _find_normalized_duplicates(
        self, tracks: list[Track]
    ) -> tuple[list[Track], list[DuplicateGroup]]:
        """
        Args:
            tracks: List of tracks to analyze.
        Returns:
            Tuple of (unique tracks, duplicate groups).
        """
        seen_keys = {}
        duplicate_groups = []

        for track in tracks:
            if not track.artists:
                continue

            key = create_track_key(track.name, track.artists[0])
            if key in seen_keys:
                seen_keys[key].append(track)
            else:
                seen_keys[key] = [track]

        unique_tracks = []
        for key, track_list in seen_keys.items():
            if len(track_list) > 1:
                duplicate_groups.append(
                    DuplicateGroup(
                        canonical=track_list[0],
                        duplicates=track_list[1:],
                        match_type="normalized",
                    )
                )
            unique_tracks.append(track_list[0])

        return unique_tracks, duplicate_groups

    def _find_fuzzy_duplicates(
        self, tracks: list[Track]
    ) -> tuple[list[Track], list[DuplicateGroup]]:
        """
        Args:
            tracks: List of tracks to analyze.
        Returns:
            Tuple of (unique tracks, duplicate groups).
        """
        duplicate_groups = []
        processed = set()

        for i, track_a in enumerate(tracks):
            if track_a.id in processed:
                continue

            if not track_a.artists:
                continue

            search_str = f"{track_a.name} {track_a.artists[0]}"
            search_str = normalize_string(search_str)

            choices = []
            choice_indices = []

            for j, track_b in enumerate(tracks):
                if i == j or track_b.id in processed:
                    continue

                if not track_b.artists:
                    continue

                choice_str = f"{track_b.name} {track_b.artists[0]}"
                choice_str = normalize_string(choice_str)
                choices.append(choice_str)
                choice_indices.append(j)

            if choices:
                results = process.extract(
                    search_str,
                    choices,
                    scorer=fuzz.token_sort_ratio,
                    score_cutoff=self.config.fuzzy_threshold,
                )

                duplicates = []
                for match, score, idx in results:
                    if score >= self.config.fuzzy_threshold:
                        track_b = tracks[choice_indices[idx]]
                        duplicates.append(track_b)
                        processed.add(track_b.id)

                if duplicates:
                    duplicate_groups.append(
                        DuplicateGroup(
                            canonical=track_a,
                            duplicates=duplicates,
                            match_type="fuzzy",
                        )
                    )
                    processed.add(track_a.id)

        unique_tracks = []
        processed_ids = set()

        for group in duplicate_groups:
            unique_tracks.append(group.canonical)
            processed_ids.add(group.canonical.id)

        for track in tracks:
            if track.id not in processed_ids:
                unique_tracks.append(track)

        return unique_tracks, duplicate_groups


def generate_duplicate_report(duplicate_groups: list[DuplicateGroup]) -> str:
    """
    Args:
        duplicate_groups: List of duplicate groups.
    Returns:
        Formatted report string.
    """
    if not duplicate_groups:
        return "No duplicates found."

    lines = ["Duplicate Report", "=" * 50, ""]

    for i, group in enumerate(duplicate_groups, 1):
        lines.append(f"{i}. {group.canonical.name} - {group.canonical.artists[0]}")
        lines.append(f"   Type: {group.match_type}")
        lines.append(f"   Duplicates ({len(group.duplicates)}):")

        for dup in group.duplicates:
            lines.append(f"     - {dup.name} - {dup.artists[0]}")

        lines.append("")

    lines.append(f"Total duplicate groups: {len(duplicate_groups)}")
    lines.append(
        f"Total duplicate tracks: {sum(len(g.duplicates) for g in duplicate_groups)}"
    )

    return "\n".join(lines)
