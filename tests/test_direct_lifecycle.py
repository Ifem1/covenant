from pathlib import Path
import datetime
import pytest

ROOT = Path(__file__).parents[1]
REGISTRY = str(ROOT / "contracts" / "covenant_registry.py")

def iso_from_unix(ts):
    return datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc).isoformat()

def setup(vm, deploy, alice, bob):
    vm.check_pickling = True
    vm.warp("2026-01-01T00:00:00+00:00")
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY))
    from genlayer.py.types import Address
    registry = deploy(REGISTRY, Address(bytes(alice)))
    module = __import__(type(registry).__module__, fromlist=["Clause", "Source"])
    recovery = Address(bytes(bob))
    clauses = [module.Clause(clause_id=1, text="availability", slash_bps=100, minimum_sources=1)]
    sources = [module.Source(source_id=1, url="https://example.com/a"), module.Source(source_id=2, url="https://example.com/b")]
    cid = registry.create_covenant("service", "description", recovery, 100, 10, 25, clauses, sources)
    vault = Address(bytes.fromhex("11" * 20))
    registry.bind_canonical_vault(vault)
    vm.sender = vault; registry.mark_funded(cid); vm.sender = alice; registry.activate(cid)
    return registry, cid, vault

def test_activation_and_due_boundaries(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, cid, vault = setup(direct_vm, direct_deploy, direct_alice, direct_bob)
    c = registry.get_covenant(cid); activation = c.activation_timestamp
    assert c.expiry_timestamp == activation + 25 and c.current_interval_start == activation and c.next_audit == activation + 10
    with pytest.raises(AssertionError): registry.activate(cid)
    direct_vm.warp(iso_from_unix(activation + 9)); assert registry.is_audit_due(cid) is False
    direct_vm.warp(iso_from_unix(activation + 10)); assert registry.is_audit_due(cid) is True
    direct_vm.warp(iso_from_unix(activation + 100)); assert registry.is_audit_due(cid) is True

def test_interval_progression_and_final_partial_interval(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, cid, _ = setup(direct_vm, direct_deploy, direct_alice, direct_bob)
    a = registry.get_covenant(cid).activation_timestamp
    registry._apply_audit_lifecycle(cid, "CLEAN", 0, a + 10); c = registry.get_covenant(cid); assert (c.current_interval_start,c.next_audit)==(a+10,a+20)
    registry._apply_audit_lifecycle(cid, "CLEAN", 0, a + 20); c = registry.get_covenant(cid); assert (c.current_interval_start,c.next_audit)==(a+20,a+25)
    registry._apply_audit_lifecycle(cid, "CLEAN", 0, a + 25); c = registry.get_covenant(cid); assert c.current_interval_start==c.expiry_timestamp and c.status=="EXPIRED"

def test_unresolved_retry_after_expiry(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, cid, _ = setup(direct_vm, direct_deploy, direct_alice, direct_bob); a=registry.get_covenant(cid).activation_timestamp
    registry._apply_audit_lifecycle(cid,"CLEAN",0,a+10); registry._apply_audit_lifecycle(cid,"CLEAN",0,a+20)
    registry._apply_audit_lifecycle(cid,"INCONCLUSIVE",0,a+25); c=registry.get_covenant(cid)
    assert c.status=="UNDER_REVIEW" and c.current_interval_start==a+20 and c.next_audit==a+25
    direct_vm.warp(iso_from_unix(a+100)); assert registry.is_audit_due(cid) is True
    registry._apply_audit_lifecycle(cid,"UNAVAILABLE",0,a+25); c=registry.get_covenant(cid); assert c.current_interval_start==a+20

def test_nonfinal_breach_continuation(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, cid, vault = setup(direct_vm, direct_deploy, direct_alice, direct_bob); a=registry.get_covenant(cid).activation_timestamp
    registry._apply_audit_lifecycle(cid,"BREACH",100,a+10); c=registry.get_covenant(cid)
    assert c.status=="BREACHED" and c.breach_count==1 and c.unsettled_breach_count==1 and c.remaining_slash_bps==9900 and c.next_audit==a+20
    direct_vm.warp(iso_from_unix(a+20)); assert registry.is_audit_due(cid) is True

def test_settlement_gated_expiry(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, cid, vault = setup(direct_vm, direct_deploy, direct_alice, direct_bob); a=registry.get_covenant(cid).activation_timestamp
    registry._apply_audit_lifecycle(cid,"BREACH",100,a+10); registry._apply_audit_lifecycle(cid,"CLEAN",0,a+20); registry._apply_audit_lifecycle(cid,"CLEAN",0,a+25)
    assert registry.refresh_expiry(cid) is False
    module=__import__(type(registry).__module__,fromlist=["Audit"]); aid="fixture"
    registry.audits[aid]=module.Audit(cid,a+10,a+20,"BREACH",[],100,"hash",False)
    direct_vm.sender=vault; registry.mark_audit_settled(aid); assert registry.get_covenant(cid).unsettled_breach_count==0; assert registry.refresh_expiry(cid) is True
    with pytest.raises(AssertionError): registry.mark_audit_settled(aid)

def test_closed_terminal_state(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry,cid,vault=setup(direct_vm,direct_deploy,direct_alice,direct_bob); c=registry.get_covenant(cid)
    with pytest.raises(AssertionError): registry.mark_closed(cid)
    registry._apply_audit_lifecycle(cid,"CLEAN",0,c.activation_timestamp+10); registry._apply_audit_lifecycle(cid,"CLEAN",0,c.activation_timestamp+20); registry._apply_audit_lifecycle(cid,"CLEAN",0,c.expiry_timestamp)
    direct_vm.sender=vault; registry.mark_closed(cid); assert registry.get_covenant(cid).status=="CLOSED" and not registry.is_audit_due(cid)
    with pytest.raises(AssertionError): registry.refresh_expiry(cid)

def test_audit_nonce_allocation(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry,cid,_=setup(direct_vm,direct_deploy,direct_alice,direct_bob); c=registry.get_covenant(cid); assert c.audit_nonce==0
    one=registry._allocate_audit_id(cid,1,2); assert registry.get_covenant(cid).audit_nonce==1
    two=registry._allocate_audit_id(cid,1,2); assert registry.get_covenant(cid).audit_nonce==2 and one!=two
    assert registry._make_audit_id(cid,1,2,0)==registry._make_audit_id(cid,1,2,0)
