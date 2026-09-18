"""Stable Opportunity Identity Module for SetuBid.

Ensures that bidder-facing card IDs remain stable across pipeline reruns,
process restarts, new duplicate arrivals, and cluster reconciliations.
"""

from __future__ import annotations
import hashlib
import uuid
from typing import Dict, List, Set, Tuple, Any, Optional
import duckdb


# Stable namespace for SetuBid opportunity cards
SETUBID_NAMESPACE = uuid.UUID("a7b3c2d1-4e5f-6a7b-8c9d-0e1f2a3b4c5d")


def generate_card_id(canonical_key: str) -> str:
    """Deterministically generates a stable card ID from a canonical cluster key."""
    # Deterministic UUID v5
    u = uuid.uuid5(SETUBID_NAMESPACE, canonical_key)
    return f"CARD-{str(u)[:16]}"


class StableIdentityManager:
    """Manages persistent opportunity/card IDs independently from source notice IDs."""

    def __init__(self, db_conn: Optional[duckdb.DuckDBPyConnection] = None):
        self.conn = db_conn
        # In-memory mapping caches: notice_id -> stable_card_id
        self.notice_to_card: Dict[str, str] = {}
        # card_id -> set of notice_ids
        self.card_to_notices: Dict[str, Set[str]] = {}
        # card_id metadata
        self.card_metadata: Dict[str, Dict[str, Any]] = {}

        if self.conn:
            self._load_from_db()

    def _load_from_db(self):
        """Loads existing clusters and card memberships from relational database."""
        try:
            rows = self.conn.execute("""
                SELECT c.stable_card_id, c.lead_notice_id, m.notice_id
                FROM dedup_clusters c
                JOIN cluster_members m ON c.cluster_id = m.cluster_id
            """).fetchall()

            for card_id, lead_id, notice_id in rows:
                self.notice_to_card[notice_id] = card_id
                if card_id not in self.card_to_notices:
                    self.card_to_notices[card_id] = set()
                    self.card_metadata[card_id] = {"lead_notice_id": lead_id}
                self.card_to_notices[card_id].add(notice_id)
        except Exception:
            # Table might not exist yet
            pass

    def assign_identities(self, raw_clusters: Dict[str, List[str]]) -> Dict[str, str]:
        """Assigns stable card IDs to clusters, preserving existing IDs whenever possible.
        
        Args:
            raw_clusters: mapping from cluster root -> sorted list of member notice_ids
            
        Returns:
            mapping of notice_id -> stable_card_id
        """
        updated_notice_to_card = {}

        for root, members in raw_clusters.items():
            # Check if any member already has an assigned card_id
            existing_card_ids = set()
            for nid in members:
                if nid in self.notice_to_card:
                    existing_card_ids.add(self.notice_to_card[nid])

            if len(existing_card_ids) == 1:
                # Exactly one existing card ID: reuse it!
                winning_card_id = list(existing_card_ids)[0]
            elif len(existing_card_ids) > 1:
                # Multiple existing clusters merged!
                # Deterministic tie-break: lowest lexicographical card_id wins
                winning_card_id = sorted(list(existing_card_ids))[0]
            else:
                # Genuinely new cluster: mint deterministic card ID based on canonical member
                canonical_member = sorted(members)[0]
                winning_card_id = generate_card_id(canonical_member)

            for nid in members:
                updated_notice_to_card[nid] = winning_card_id

        # Update in-memory state
        self.notice_to_card.update(updated_notice_to_card)
        self.card_to_notices.clear()
        for nid, cid in self.notice_to_card.items():
            if cid not in self.card_to_notices:
                self.card_to_notices[cid] = set()
            self.card_to_notices[cid].add(nid)

        if self.conn:
            self._save_to_db()

        return updated_notice_to_card

    def _save_to_db(self):
        """Persists clusters and memberships into DuckDB."""
        if not self.conn:
            return

        cluster_rows = []
        member_rows = []
        for card_id, members in self.card_to_notices.items():
            lead_id = sorted(list(members))[0]
            cluster_id = f"CLUST-{card_id[5:]}"
            cluster_rows.append((cluster_id, card_id, lead_id))
            for nid in members:
                member_rows.append((cluster_id, nid, "UNKNOWN", "2024-01-01"))

        # Upsert
        self.conn.execute("DELETE FROM cluster_members")
        self.conn.execute("DELETE FROM dedup_clusters")

        if cluster_rows:
            self.conn.executemany("""
                INSERT INTO dedup_clusters (cluster_id, stable_card_id, lead_notice_id)
                VALUES (?, ?, ?)
            """, cluster_rows)

        if member_rows:
            self.conn.executemany("""
                INSERT INTO cluster_members (cluster_id, notice_id, portal_id, published_at)
                VALUES (?, ?, ?, ?)
            """, member_rows)

    def get_card_id(self, notice_id: str) -> Optional[str]:
        return self.notice_to_card.get(notice_id)

    def get_members(self, card_id: str) -> Set[str]:
        return self.card_to_notices.get(card_id, set())
