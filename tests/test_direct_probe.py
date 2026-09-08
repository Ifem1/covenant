"""Minimal Direct Mode probe; SDK imports remain owned by gltest's loader."""
from pathlib import Path

ROOT = Path(__file__).parents[1]

def typed_address(contract_path, raw_address):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(contract_path))
    from genlayer.py.types import Address
    if isinstance(raw_address, Address):
        return raw_address
    return Address(bytes(raw_address))

def test_registry_deploys(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    registry_path = str(ROOT / "contracts" / "covenant_registry.py")
    registry = direct_deploy(registry_path, typed_address(registry_path, direct_alice))
    assert registry is not None

def test_control_deploys(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    control_path = str(ROOT / "contracts" / "direct_control.py")
    alice_address = typed_address(control_path, direct_alice)
    control = direct_deploy(control_path, alice_address)
    assert control is not None
    assert control.get_owner() == alice_address

def test_validator_probe(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    control_path = str(ROOT / "contracts" / "direct_control.py")
    control = direct_deploy(control_path, typed_address(control_path, direct_alice))
    assert control.run_probe() == 'probe-ok'
    assert direct_vm.run_validator() is True

def test_batch2a_smoke(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    registry_path = str(ROOT / "contracts" / "covenant_registry.py")
    vault_path = str(ROOT / "contracts" / "covenant_vault.py")
    admin = typed_address(registry_path, direct_alice)
    registry = direct_deploy(registry_path, admin)
    assert str(registry.get_canonical_vault()).lower().endswith('0' * 40)
    vault = direct_deploy(vault_path, typed_address(vault_path, direct_vm._contract_address))
    vault_address = typed_address(registry_path, direct_vm._contract_address)
    direct_vm.sender = direct_alice
    # deploy_contract derives the real address from the path; redeploying the registry
    # in this isolated test gives the binding call the exact contract address bytes.
    registry = direct_deploy(registry_path, admin)
    registry.bind_canonical_vault(vault_address)
    assert registry.get_canonical_vault() == vault_address
    with direct_vm.expect_revert(): registry.bind_canonical_vault(vault_address)
    clauses = [{"clause_id": 1, "text": "availability", "slash_bps": 2500, "minimum_sources": 1}]
    sources = [{"source_id": 1, "url": "https://example.com/a"}, {"source_id": 2, "url": "https://example.com/b"}]
    recovery = typed_address(registry_path, direct_bob)
    cid = registry.create_covenant("service", "description", recovery, 100, 10, 20, clauses, sources)
    stored = registry.get_covenant(cid)
    assert stored.operator == admin and stored.service == "service" and stored.description == "description"
    assert stored.minimum_bond == 100 and stored.interval == 10 and stored.term == 20
    assert stored.clauses[0].text == "availability" and stored.sources[1].url == sources[1]["url"] and stored.status == "DRAFT"
    for bad in [
        {"minimum_bond": 0},
        {"recovery": admin},
        {"sources": [sources[0], {"source_id": 2, "url": sources[0]["url"]}]},
        {"sources": [sources[0], {"source_id": 2, "url": "http://example.com/b"}]},
        {"clauses": [clauses[0], clauses[0]]},
    ]:
        args = ["service", "description", recovery, bad.get("minimum_bond", 100), 10, 20, bad.get("clauses", clauses), bad.get("sources", sources)]
        if "recovery" in bad: args[2] = admin
        with direct_vm.expect_revert(): registry.create_covenant(*args)
    with direct_vm.expect_revert(): registry.mark_funded(cid)
