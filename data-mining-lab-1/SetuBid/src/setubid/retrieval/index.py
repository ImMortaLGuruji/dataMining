"""LSH Banding Index Module for SetuBid.

Implements Locality Sensitive Hashing (LSH) over MinHash signatures using
b bands of r rows (m = b * r).
"""

from __future__ import annotations
import hashlib
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any, Optional
import numpy as np


class LSHIndex:
    """In-memory LSH Banding Index."""

    def __init__(self, num_bands: int = 32, rows_per_band: int = 8):
        self.num_bands = num_bands
        self.rows_per_band = rows_per_band
        self.num_hashes = num_bands * rows_per_band
        
        # Buckets: band_idx -> bucket_key -> set of notice_ids
        self.buckets: List[Dict[int, Set[str]]] = [defaultdict(set) for _ in range(num_bands)]
        # Map notice_id -> bands bucket keys
        self.notice_keys: Dict[str, List[int]] = {}

    def _hash_band(self, band_slice: np.ndarray) -> int:
        """Hashes an r-dimensional integer subvector to a 64-bit integer bucket key."""
        # Convert subvector bytes to 64-bit hash
        digest = hashlib.blake2b(band_slice.tobytes(), digest_size=8).digest()
        return int.from_bytes(digest, byteorder="little", signed=False)

    def insert(self, notice_id: str, signature: np.ndarray):
        """Inserts a notice's signature into the LSH index."""
        if len(signature) < self.num_hashes:
            raise ValueError(f"Signature length {len(signature)} < required {self.num_hashes}")

        keys = []
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            end = start + self.rows_per_band
            band_slice = signature[start:end]
            b_key = self._hash_band(band_slice)
            keys.append(b_key)
            self.buckets[band_idx][b_key].add(notice_id)
        
        self.notice_keys[notice_id] = keys

    def query_candidates(self, notice_id: str, signature: Optional[np.ndarray] = None, candidate_cap: Optional[int] = None) -> Set[str]:
        """Queries the index for candidate notice_ids colliding in at least one band."""
        candidates = set()
        
        if signature is not None:
            for band_idx in range(self.num_bands):
                start = band_idx * self.rows_per_band
                end = start + self.rows_per_band
                b_key = self._hash_band(signature[start:end])
                candidates.update(self.buckets[band_idx].get(b_key, set()))
        elif notice_id in self.notice_keys:
            keys = self.notice_keys[notice_id]
            for band_idx, b_key in enumerate(keys):
                candidates.update(self.buckets[band_idx].get(b_key, set()))
        else:
            return set()

        # Remove self
        candidates.discard(notice_id)

        if candidate_cap is not None and len(candidates) > candidate_cap:
            # Cap candidates if requested
            return set(list(candidates)[:candidate_cap])

        return candidates

    def theoretical_collision_prob(self, similarity: float) -> float:
        """Calculates theoretical probability of retrieving a pair with given similarity s:
        
        P(collision) = 1 - (1 - s^r)^b
        """
        s = float(np.clip(similarity, 0.0, 1.0))
        return 1.0 - (1.0 - (s ** self.rows_per_band)) ** self.num_bands
