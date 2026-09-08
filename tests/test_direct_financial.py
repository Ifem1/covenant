from pathlib import Path

ROOT=Path(__file__).parents[1]
VAULT=str(ROOT/"contracts"/"covenant_vault.py")

def test_original_principal_slash_arithmetic(direct_vm,direct_deploy,direct_alice):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(VAULT))
    from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.sender=direct_alice
    vault=direct_deploy(VAULT,Address(bytes.fromhex("22"*20)))
    cid=1; vault.principal[cid]=1000; vault.bonds[cid]=1000
    first=vault._target_slashed(cid,2500); second=vault._target_slashed(cid,5000); final=vault._target_slashed(cid,10000)
    assert first==250 and second==500 and final==1000
    assert second-first==250 and final-second==500

def test_staged_state_defaults_are_zero(direct_vm,direct_deploy,direct_alice):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(VAULT))
    from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.sender=direct_alice
    vault=direct_deploy(VAULT,Address(bytes.fromhex("22"*20)))
    assert vault.get_bond(1)==0
    assert vault.pending_slash_count.get(1,0)==0
    assert vault.consumed_slash_bps.get(1,0)==0
