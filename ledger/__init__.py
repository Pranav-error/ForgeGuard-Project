"""ForgeGuard -- Ledger module (Phase 2: blockchain-style anchoring, Gap 9 / O9)."""
from .chain import Block, GENESIS_HASH, make_block, verify_links

__all__ = ["Block", "GENESIS_HASH", "make_block", "verify_links"]
