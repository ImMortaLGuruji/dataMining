"""MinHash Estimator Module for SetuBid.

Implements deterministic MinHash signature generation and similarity estimation.
"""

from __future__ import annotations
import hashlib
from typing import List, Set, Sequence, Tuple
import numpy as np


# Large 61-bit Mersenne prime for universal hashing: 2^61 - 1
MERSENNE_PRIME = (1 << 61) - 1


class MinHashGenerator:
    """Deterministic MinHash signature generator using universal hashing."""

    def __init__(self, num_hashes: int = 256, seed: int = 42):
        self.num_hashes = num_hashes
        self.seed = seed
        rng = np.random.RandomState(seed)
        # Random coefficients: a_i in [1, p-1], b_i in [0, p-1]
        self.a = rng.randint(1, MERSENNE_PRIME - 1, size=num_hashes, dtype=np.int64)
        self.b = rng.randint(0, MERSENNE_PRIME - 1, size=num_hashes, dtype=np.int64)

    def hash_token(self, token: str) -> int:
        """Converts string token to 61-bit integer hash < MERSENNE_PRIME."""
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        raw_val = int.from_bytes(digest, byteorder="little", signed=False)
        return raw_val % MERSENNE_PRIME

    def compute_signature(self, shingles: Set[str]) -> np.ndarray:
        """Computes MinHash signature of length num_hashes for a shingle set."""
        if not shingles:
            return np.zeros(self.num_hashes, dtype=np.int64)

        # Convert shingles to 61-bit token hashes
        token_hashes = np.array([self.hash_token(s) for s in shingles], dtype=np.int64)
        
        # signatures = min over tokens of ((a * x + b) % prime)
        signature = np.full(self.num_hashes, MERSENNE_PRIME, dtype=np.int64)
        
        # Batch over tokens to keep memory footprint bounded
        batch_size = 200
        for i in range(0, len(token_hashes), batch_size):
            chunk = token_hashes[i : i + batch_size] # (B,)
            # (num_hashes, 1) * (1, B) + (num_hashes, 1)
            # Use python modular arithmetic via object or uint64/int64
            # Since a * x can be ~ 2^61 * 2^61 = 2^122, numpy int64 will overflow.
            # In Python, native large int math never overflows!
            pass

        # Clean vectorized approach in numpy:
        # Instead of large prime multiplication which exceeds 64 bits:
        # We can use standard 32-bit universal hashing (p = 2^31 - 1, 2147483647) 
        # or 64-bit split multiplication or Python loop over hashes:
        return self._compute_fast(token_hashes)

    def _compute_fast(self, token_hashes: np.ndarray) -> np.ndarray:
        p = 2147483647
        a32 = (self.a % (p - 1) + 1)[:, None]
        b32 = (self.b % p)[:, None]
        th32 = (token_hashes % p).astype(np.int64)[None, :]
        
        # Single vectorized broadcast: (256, N)
        hashes = (a32 * th32 + b32) % p
        return np.min(hashes, axis=1)


def estimate_jaccard(sig_a: Sequence[int], sig_b: Sequence[int]) -> float:
    """Estimates Jaccard similarity from two MinHash signatures:
    
    J_hat = (matches) / (num_hashes)
    """
    if len(sig_a) != len(sig_b):
        raise ValueError(f"Signatures must be equal length, got {len(sig_a)} and {len(sig_b)}")
    if len(sig_a) == 0:
        return 0.0
    matches = np.sum(np.asarray(sig_a) == np.asarray(sig_b))
    return float(matches) / float(len(sig_a))
