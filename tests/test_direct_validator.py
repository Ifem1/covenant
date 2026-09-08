from pathlib import Path

ROOT = Path(__file__).parents[1]
CONTROL = str(ROOT / "contracts" / "direct_control.py")

def typed_address(path, raw):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(path))
    from genlayer.py.types import Address
    return raw if isinstance(raw, Address) else Address(bytes(raw))

def test_control_and_validator(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    control = direct_deploy(CONTROL, typed_address(CONTROL, direct_alice))
    assert control.run_probe() == "probe-ok"
    assert direct_vm.run_validator() is True
