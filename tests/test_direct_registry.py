from pathlib import Path

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

def test_registry_deploys_and_starts_unbound(direct_vm, direct_deploy, direct_alice):
    registry = deploy(direct_vm, direct_deploy, direct_alice)
    assert registry is not None
    assert str(registry.get_canonical_vault()).lower().endswith("0" * 40)

def test_binding_authorization_and_storage_roundtrip(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry = deploy(direct_vm, direct_deploy, direct_alice)
    vault = typed_address(REGISTRY, bytes.fromhex("11" * 20))
    registry.bind_canonical_vault(vault)
    assert registry.get_canonical_vault() == vault
    with direct_vm.expect_revert(): registry.bind_canonical_vault(vault)
    direct_vm.sender = direct_bob
    other = typed_address(REGISTRY, bytes.fromhex("22" * 20))
    fresh = deploy(direct_vm, direct_deploy, direct_alice)
    with direct_vm.expect_revert(): fresh.bind_canonical_vault(other)
    direct_vm.sender = direct_alice
    args, clauses, sources = definition(direct_alice, direct_bob)
    cid = registry.create_covenant(*args)
    stored = registry.get_covenant(cid)
    assert stored.operator == typed_address(REGISTRY, direct_alice)
    assert stored.service == "service" and stored.description == "description"
    assert stored.recovery == typed_address(REGISTRY, direct_bob)
    assert stored.minimum_bond == 100 and stored.interval == 10 and stored.term == 20 and stored.status == "DRAFT"
    assert stored.clauses[0].text == clauses[0]["text"] and stored.sources[1].url == sources[1]["url"]
    assert stored.definition_hash == registry.get_covenant(cid).definition_hash and stored.definition_hash

def test_creation_rejections_and_callback_auth(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry = deploy(direct_vm, direct_deploy, direct_alice)
    recovery = typed_address(REGISTRY, direct_bob)
    args, clauses, sources = definition(direct_alice, recovery)
    cases = [
        args[:2] + [recovery, 0, 10, 20, clauses, sources],
        args[:2] + [typed_address(REGISTRY, direct_alice), 100, 10, 20, clauses, sources],
        args[:2] + [recovery, 100, 10, 20, clauses, [sources[0], {"source_id": 2, "url": sources[0]["url"]}]],
        args[:2] + [recovery, 100, 10, 20, clauses, [sources[0], {"source_id": 2, "url": "http://example.com/b"}]],
        args[:2] + [recovery, 100, 10, 20, [clauses[0], clauses[0]], sources],
    ]
    for bad in cases:
        with direct_vm.expect_revert(): registry.create_covenant(*bad)
    cid = registry.create_covenant(*args)
    with direct_vm.expect_revert(): registry.mark_funded(cid)
