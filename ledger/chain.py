"""Hash-chain ledger -- Phase 2, Gap 9 / O9 (blockchain anchoring).

# ponytail: a local, permissioned hash chain (each block links to the
# previous block's hash, same mechanism a blockchain uses internally),
# not a public/distributed ledger -- there is no consensus, no network, no
# smart contract. It gives the real property Gap 9 asked for (a verified
# document's hash becomes tamper-evident: altering any past block breaks
# every hash after it, and verify_chain() below detects exactly that).
# Anchoring to a public chain (Ethereum/Hyperledger, papers [50], [51])
# means swapping append()'s storage call for a transaction call; the block
# shape and verify_chain() contract stay the same.
"""
import hashlib
from dataclasses import dataclass

GENESIS_HASH = "0" * 64


@dataclass
class Block:
    index: int
    document_id: str
    verification_id: str
    document_hash: str   # the document's own SHA-256 (FR-P2)
    prev_hash: str
    created_at: str
    block_hash: str = ""

    def compute_hash(self) -> str:
        payload = f"{self.index}|{self.document_id}|{self.verification_id}|{self.document_hash}|{self.prev_hash}|{self.created_at}"
        return hashlib.sha256(payload.encode()).hexdigest()


def make_block(index: int, document_id: str, verification_id: str, document_hash: str, prev_hash: str, created_at: str) -> Block:
    block = Block(index, document_id, verification_id, document_hash, prev_hash, created_at)
    block.block_hash = block.compute_hash()
    return block


def verify_links(blocks: list[Block]) -> tuple[bool, int | None]:
    """Walk the chain recomputing each block's hash and checking the linkage.
    Returns (valid, first_broken_index). An empty chain is valid."""
    prev_hash = GENESIS_HASH
    for block in blocks:
        if block.prev_hash != prev_hash:
            return False, block.index
        if block.compute_hash() != block.block_hash:
            return False, block.index
        prev_hash = block.block_hash
    return True, None
