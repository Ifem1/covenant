from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1]
REGISTRY = str(ROOT / "contracts" / "covenant_registry.py")

def typed_address(path, raw):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(path))
    from genlayer.py.types import Address
    return raw if isinstance(raw, Address) else Address(bytes(raw))

def deploy(vm, factory, alice):
    vm.sender = alice; vm.check_pickling = True
    return factory(REGISTRY, typed_address(REGISTRY, alice))

def definition(operator, recovery):
    clauses = [{"clause_id": 1, "text": "availability", "slash_bps": 2500, "minimum_sources": 1}]
    sources = [{"source_id": 1, "url": "https://example.com/a"}, {"source_id": 2, "url": "https://example.com/b"}]
    return ["service", "description", recovery, 100, 10, 20, clauses, sources], clauses, sources

def test_registry_foundation_and_storage(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry = deploy(direct_vm, direct_deploy, direct_alice)
    assert registry is not None
    assert str(registry.get_canonical_vault()).lower().endswith("0" * 40)
    vault = typed_address(REGISTRY, bytes.fromhex("11" * 20))
    # Test authorization while the registry is still unbound.
    direct_vm.sender = direct_bob
    with pytest.raises(AssertionError): registry.bind_canonical_vault(vault)
    direct_vm.sender = direct_alice
    registry.bind_canonical_vault(vault)
    assert registry.get_canonical_vault() == vault
    with pytest.raises(AssertionError): registry.bind_canonical_vault(vault)
    args, clauses, sources = definition(direct_alice, direct_bob)
    cid = registry.create_covenant(*args)
    stored = registry.get_covenant(cid)
    assert stored.operator == typed_address(REGISTRY, direct_alice)
    assert stored.service == "service" and stored.description == "description"
    assert stored.recovery == typed_address(REGISTRY, direct_bob)
    assert stored.minimum_bond == 100 and stored.interval == 10 and stored.term == 20 and stored.status == "DRAFT"
    assert len(stored.clauses) == 1 and stored.clauses[0].clause_id == 1
    assert stored.clauses[0].text == clauses[0]["text"] and stored.clauses[0].slash_bps == 2500
    assert stored.clauses[0].minimum_sources == 1
    assert len(stored.sources) == 2 and stored.sources[0].source_id == 1 and stored.sources[1].source_id == 2
    assert stored.sources[0].url == sources[0]["url"] and stored.sources[1].url == sources[1]["url"]
    assert stored.definition_hash == registry.get_covenant(cid).definition_hash and stored.definition_hash
    recovery = typed_address(REGISTRY, direct_bob)
    args, clauses, sources = definition(direct_alice, recovery)
    cases = [
        args[:2] + [recovery, 0, 10, 20, clauses, sources],
        args[:2] + [typed_address(REGISTRY, direct_alice), 100, 10, 20, clauses, sources],
        args[:2] + [recovery, 100, 10, 20, clauses, [sources[0], {"source_id": 2, "url": sources[0]["url"]}]],
        args[:2] + [recovery, 100, 10, 20, clauses, [sources[0], {"source_id": 2, "url": "http://example.com/b"}]],
        args[:2] + [recovery, 100, 10, 20, [clauses[0], clauses[0]], sources],
    ]
    labels = ["zero-bond", "self-recovery", "duplicate-url", "non-https", "duplicate-clause-id"]
    for label, bad in zip(labels, cases):
        with pytest.raises(AssertionError, match=""):
            registry.create_covenant(*bad)
    cid = registry.create_covenant(*args)
    direct_vm.sender = direct_bob
    with pytest.raises(AssertionError): registry.mark_funded(cid)
