from pathlib import Path

ROOT = Path(__file__).parents[1]
VAULT = str(ROOT / "contracts" / "covenant_vault.py")

def typed_address(path, raw):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(path))
    from genlayer.py.types import Address
    return raw if isinstance(raw, Address) else Address(bytes(raw))

def test_vault_deploys_and_initial_storage(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.check_pickling = True
    registry = typed_address(VAULT, bytes.fromhex("33" * 20))
    vault = direct_deploy(VAULT, registry)
    assert vault is not None
    assert vault.get_bond(999) == 0
    assert vault.registry == registry
