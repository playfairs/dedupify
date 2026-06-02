from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    id: str
    name: str
    artists: list[str]
    url: str
    is_local: bool = False

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Track):
            return False
        return self.id == other.id


@dataclass
class Playlist:
    id: str
    name: str
    url: str
    tracks: list[Track] = field(default_factory=list)
    snapshot_id: Optional[str] = None


@dataclass
class DedupeStats:
    total_tracks: int = 0
    unique_tracks: int = 0
    duplicates_removed: int = 0
    exact_matches: int = 0
    normalized_matches: int = 0
    fuzzy_matches: int = 0

    def __str__(self) -> str:
        return (
            f"Total tracks: {self.total_tracks}\n"
            f"Unique tracks: {self.unique_tracks}\n"
            f"Duplicates removed: {self.duplicates_removed}\n"
            f"Exact matches: {self.exact_matches}\n"
            f"Normalized matches: {self.normalized_matches}\n"
            f"Fuzzy matches: {self.fuzzy_matches}"
        )


@dataclass
class DuplicateGroup:
    canonical: Track
    duplicates: list[Track]
    match_type: str
