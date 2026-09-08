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
    direct_vm.mock_web("https://example.test", "stable evidence")
    direct_vm.mock_llm("probe", "[]")
    registry = direct_deploy(str(ROOT / "contracts" / "covenant_registry.py"), direct_alice)
    assert registry is not None
    assert direct_vm.run_validator(leader_result=[]) in (True, False)
