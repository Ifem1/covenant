from pathlib import Path
import json
import pytest

ROOT=Path(__file__).parents[1]
REGISTRY=str(ROOT/"contracts"/"covenant_registry.py")

def test_public_run_audit_clean_persists_evidence(direct_vm,direct_deploy,direct_alice,direct_bob):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY))
    from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.warp("2026-01-01T00:00:00+00:00"); direct_vm.sender=direct_alice
    registry=direct_deploy(REGISTRY,Address(bytes(direct_alice)))
    module=__import__(type(registry).__module__,fromlist=["Clause","Source"])
    recovery=Address(bytes(direct_bob)); clauses=[module.Clause(clause_id=1,text="availability",slash_bps=100,minimum_sources=1)]
    sources=[module.Source(source_id=1,url="https://example.com/a"),module.Source(source_id=2,url="https://example.com/b")]
    cid=registry.create_covenant("service","description",recovery,100,10,10,clauses,sources)
    vault=Address(bytes.fromhex("11"*20)); registry.bind_canonical_vault(vault); direct_vm.sender=vault; registry.mark_funded(cid); direct_vm.sender=direct_alice; registry.activate(cid)
    body="availability was verified"
    direct_vm.mock_web("example\\.com",{"status":200,"body":body})
    response=json.dumps([{"clause_id":1,"finding":"COMPLIED","severity":"NONE","evidence":[{"source_id":1,"excerpt":body}],"observed_event_timestamp":0,"reason":"supported"}])
    direct_vm.mock_llm("FROZEN",response)
    direct_vm.warp("2026-01-01T00:00:10+00:00")
    audit_id=registry.run_audit(cid)
    audit=registry.get_audit(audit_id)
    assert audit.outcome=="CLEAN" and audit.slash_bps==0 and audit.interval_start==registry.get_covenant(cid).activation_timestamp
    assert len(audit.findings)==1 and len(audit.findings[0].evidence)==1 and audit.findings[0].evidence[0].source_id==1

def test_public_run_audit_breach_and_persistence(direct_vm,direct_deploy,direct_alice,direct_bob):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY)); from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.warp("2026-01-01T00:00:00+00:00"); direct_vm.sender=direct_alice
    registry=direct_deploy(REGISTRY,Address(bytes(direct_alice))); module=__import__(type(registry).__module__,fromlist=["Clause","Source"])
    recovery=Address(bytes(direct_bob)); clause=module.Clause(clause_id=1,text="availability",slash_bps=250,minimum_sources=1); sources=[module.Source(source_id=1,url="https://example.com/a"),module.Source(source_id=2,url="https://example.com/b")]
    cid=registry.create_covenant("service","description",recovery,100,10,10,[clause],sources); vault=Address(bytes.fromhex("11"*20)); registry.bind_canonical_vault(vault); direct_vm.sender=vault; registry.mark_funded(cid); direct_vm.sender=direct_alice; registry.activate(cid)
    body="outage at the service"; direct_vm.mock_web("example\\.com",{"status":200,"body":body}); response=json.dumps([{"clause_id":1,"finding":"BREACHED","severity":"HIGH","evidence":[{"source_id":1,"excerpt":body}],"observed_event_timestamp":1767225605,"reason":"outage"}]); direct_vm.mock_llm("FROZEN",response); direct_vm.warp("2026-01-01T00:00:10+00:00")
    audit=registry.get_audit(registry.run_audit(cid)); stored=registry.get_covenant(cid)
    assert audit.outcome=="BREACH" and audit.slash_bps==250 and audit.findings[0].finding=="BREACHED" and audit.findings[0].evidence[0].source_id==1 and audit.findings[0].evidence[0].excerpt==body and audit.findings[0].observed_event_timestamp==1767225605
    assert stored.breach_count==1 and stored.unsettled_breach_count==1 and stored.status=="BREACHED"

def _run_unresolved(direct_vm,direct_deploy,direct_alice,direct_bob,outcome):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY)); from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.warp("2026-01-01T00:00:00+00:00"); direct_vm.sender=direct_alice
    registry=direct_deploy(REGISTRY,Address(bytes(direct_alice))); module=__import__(type(registry).__module__,fromlist=["Clause","Source"]); recovery=Address(bytes(direct_bob)); clause=module.Clause(clause_id=1,text="availability",slash_bps=100,minimum_sources=1); sources=[module.Source(source_id=1,url="https://example.com/a"),module.Source(source_id=2,url="https://example.com/b")]
    cid=registry.create_covenant("service","description",recovery,100,10,10,[clause],sources); vault=Address(bytes.fromhex("11"*20)); registry.bind_canonical_vault(vault); direct_vm.sender=vault; registry.mark_funded(cid); direct_vm.sender=direct_alice; registry.activate(cid); direct_vm.mock_web("example\\.com",{"status":200,"body":"no evidence"})
    direct_vm.mock_llm("FROZEN",json.dumps([{"clause_id":1,"finding":outcome,"severity":"NONE","evidence":[],"observed_event_timestamp":0,"reason":"unresolved"}])); direct_vm.warp("2026-01-01T00:00:10+00:00"); aid=registry.run_audit(cid); audit=registry.get_audit(aid); c=registry.get_covenant(cid); assert audit.outcome==outcome and len(audit.findings[0].evidence)==0 and audit.findings[0].observed_event_timestamp==0 and c.status=="UNDER_REVIEW" and c.current_interval_start==c.activation_timestamp

def test_public_run_audit_inconclusive(direct_vm,direct_deploy,direct_alice,direct_bob):
    _run_unresolved(direct_vm,direct_deploy,direct_alice,direct_bob,"INCONCLUSIVE")

def test_public_run_audit_unavailable(direct_vm,direct_deploy,direct_alice,direct_bob):
    _run_unresolved(direct_vm,direct_deploy,direct_alice,direct_bob,"UNAVAILABLE")

def test_public_run_audit_rejects_fabricated_and_out_of_window_evidence(direct_vm,direct_deploy,direct_alice,direct_bob):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY)); from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.warp("2026-01-01T00:00:00+00:00"); direct_vm.sender=direct_alice
    registry=direct_deploy(REGISTRY,Address(bytes(direct_alice))); module=__import__(type(registry).__module__,fromlist=["Clause","Source"]); recovery=Address(bytes(direct_bob)); clause=module.Clause(clause_id=1,text="availability",slash_bps=100,minimum_sources=1); sources=[module.Source(source_id=1,url="https://example.com/a"),module.Source(source_id=2,url="https://example.com/b")]
    cid=registry.create_covenant("service","description",recovery,100,10,10,[clause],sources); vault=Address(bytes.fromhex("11"*20)); registry.bind_canonical_vault(vault); direct_vm.sender=vault; registry.mark_funded(cid); direct_vm.sender=direct_alice; registry.activate(cid); direct_vm.mock_web("example\\.com",{"status":200,"body":"grounded"})
    direct_vm.mock_llm("FROZEN",json.dumps([{"clause_id":1,"finding":"BREACHED","severity":"HIGH","evidence":[{"source_id":1,"excerpt":"fabricated"}],"observed_event_timestamp":1767225605,"reason":"bad"}])); direct_vm.warp("2026-01-01T00:00:10+00:00")
    with pytest.raises(AssertionError): registry.run_audit(cid)
    direct_vm.clear_mocks(); direct_vm.mock_web("example\\.com",{"status":200,"body":"grounded"})
    direct_vm.mock_llm("FROZEN",json.dumps([{"clause_id":1,"finding":"BREACHED","severity":"HIGH","evidence":[{"source_id":1,"excerpt":"grounded"}],"observed_event_timestamp":1767225700,"reason":"late"}]))
    with pytest.raises(AssertionError): registry.run_audit(cid)

def test_public_run_audit_rejects_verifier_disagreement(direct_vm,direct_deploy,direct_alice,direct_bob):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY)); from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.warp("2026-01-01T00:00:00+00:00"); direct_vm.sender=direct_alice
    registry=direct_deploy(REGISTRY,Address(bytes(direct_alice))); module=__import__(type(registry).__module__,fromlist=["Clause","Source"]); recovery=Address(bytes(direct_bob)); clause=module.Clause(clause_id=1,text="availability",slash_bps=100,minimum_sources=1); sources=[module.Source(source_id=1,url="https://example.com/a"),module.Source(source_id=2,url="https://example.com/b")]
    cid=registry.create_covenant("service","description",recovery,100,10,10,[clause],sources); vault=Address(bytes.fromhex("11"*20)); registry.bind_canonical_vault(vault); direct_vm.sender=vault; registry.mark_funded(cid); direct_vm.sender=direct_alice; registry.activate(cid); direct_vm.mock_web("example\\.com",{"status":200,"body":"grounded"})
    direct_vm.mock_llm("FROZEN CONTRACT",json.dumps([{"clause_id":1,"finding":"COMPLIED","severity":"NONE","evidence":[{"source_id":1,"excerpt":"grounded"}],"observed_event_timestamp":0,"reason":"ok"}]))
    direct_vm.mock_llm("VERIFIER",json.dumps([{"clause_id":1,"finding":"BREACHED"}]))
    direct_vm.warp("2026-01-01T00:00:10+00:00")
    with pytest.raises(AssertionError): registry.run_audit(cid)
