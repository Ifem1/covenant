from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1]
REGISTRY = str(ROOT / "contracts" / "covenant_registry.py")

def typed(path, raw):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(path))
    from genlayer.py.types import Address
    return raw if isinstance(raw, Address) else Address(bytes(raw))

def test_lifecycle_scheduling_and_expiry_guard(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.check_pickling = True
    direct_vm.sender = direct_alice
    registry = direct_deploy(REGISTRY, typed(REGISTRY, direct_alice))
    module = __import__(type(registry).__module__, fromlist=["Clause", "Source"])
    recovery = typed(REGISTRY, direct_bob)
    clauses = [module.Clause(clause_id=1, text="availability", slash_bps=100, minimum_sources=1)]
    sources = [module.Source(source_id=1, url="https://example.com/a"), module.Source(source_id=2, url="https://example.com/b")]
    cid = registry.create_covenant("service", "description", recovery, 100, 10, 25, clauses, sources)
    assert registry.refresh_expiry(cid) is False
    with pytest.raises(AssertionError): registry.activate(cid)
    vault = typed(REGISTRY, bytes.fromhex("11" * 20))
    registry.bind_canonical_vault(vault)
    registry.mark_funded(cid)
    registry.activate(cid)
    c = registry.get_covenant(cid)
    assert c.activation_timestamp > 0 and c.expiry_timestamp == c.activation_timestamp + 25
    assert c.current_interval_start == c.activation_timestamp
    assert c.next_audit == min(c.activation_timestamp + 10, c.expiry_timestamp)
    direct_vm.warp(c.next_audit)
    assert registry.is_audit_due(cid) is True
    direct_vm.warp(c.expiry_timestamp + 100)
    assert registry.refresh_expiry(cid) is False
