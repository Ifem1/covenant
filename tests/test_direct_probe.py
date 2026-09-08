"""Minimal Direct Mode probe; SDK imports remain owned by gltest's loader."""
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_registry_deploys(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    registry = direct_deploy(str(ROOT / "contracts" / "covenant_registry.py"), direct_alice)
    assert registry is not None

def test_control_deploys(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    control = direct_deploy(str(ROOT / "contracts" / "direct_control.py"), direct_alice)
    assert control is not None
    assert control.get_owner() == direct_alice

def test_validator_probe(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.mock_web("https://example.test", "stable evidence")
    direct_vm.mock_llm("probe", "[]")
    registry = direct_deploy(str(ROOT / "contracts" / "covenant_registry.py"), direct_alice)
    assert registry is not None
    assert direct_vm.run_validator(leader_result=[]) in (True, False)
