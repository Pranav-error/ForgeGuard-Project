"""Self-check: python3 -m ledger.test_module"""
from .chain import GENESIS_HASH, make_block, verify_links


def test_single_block_links_to_genesis():
    b = make_block(0, "doc1", "ver1", "a" * 64, GENESIS_HASH, "2026-01-01T00:00:00")
    valid, broken = verify_links([b])
    assert valid and broken is None


def test_chain_of_blocks_valid():
    b0 = make_block(0, "doc1", "ver1", "a" * 64, GENESIS_HASH, "t0")
    b1 = make_block(1, "doc2", "ver2", "b" * 64, b0.block_hash, "t1")
    b2 = make_block(2, "doc3", "ver3", "c" * 64, b1.block_hash, "t2")
    valid, broken = verify_links([b0, b1, b2])
    assert valid and broken is None


def test_tampering_a_past_block_breaks_the_chain():
    b0 = make_block(0, "doc1", "ver1", "a" * 64, GENESIS_HASH, "t0")
    b1 = make_block(1, "doc2", "ver2", "b" * 64, b0.block_hash, "t1")
    b2 = make_block(2, "doc3", "ver3", "c" * 64, b1.block_hash, "t2")
    # simulate someone editing block 0's stored document hash after the fact
    b0.document_hash = "f" * 64
    valid, broken = verify_links([b0, b1, b2])
    assert valid is False
    assert broken == 0  # b0's own hash no longer matches its recomputed hash


def test_broken_linkage_detected():
    b0 = make_block(0, "doc1", "ver1", "a" * 64, GENESIS_HASH, "t0")
    b1 = make_block(1, "doc2", "ver2", "b" * 64, "wrong-prev-hash", "t1")
    valid, broken = verify_links([b0, b1])
    assert valid is False and broken == 1


def test_empty_chain_is_valid():
    valid, broken = verify_links([])
    assert valid and broken is None


def main():
    test_single_block_links_to_genesis()
    test_chain_of_blocks_valid()
    test_tampering_a_past_block_breaks_the_chain()
    test_broken_linkage_detected()
    test_empty_chain_is_valid()
    print("all demo checks passed")


if __name__ == "__main__":
    main()
