from pathlib import Path
import pytest

ROOT=Path(__file__).parents[1]
REGISTRY=str(ROOT/"contracts"/"covenant_registry.py")

def test_evidence_validation_rules(direct_vm,direct_deploy,direct_alice):
    from gltest.direct.sdk_loader import setup_sdk_paths
    setup_sdk_paths(Path(REGISTRY))
    from genlayer.py.types import Address
    direct_vm.check_pickling=True; direct_vm.sender=direct_alice
    registry=direct_deploy(REGISTRY,Address(bytes(direct_alice)))
    module=__import__(type(registry).__module__,fromlist=["Source"])
    sources=[module.Source(source_id=1,url="https://a"),module.Source(source_id=2,url="https://b")]
    fetched={1:"availability was 98.5 percent",2:"service experienced 17 minutes of downtime"}
    assert registry._validate_evidence([{"source_id":1,"excerpt":"availability was 98.5 percent"}],sources,fetched,1)==[1]
    assert registry._validate_evidence([{"source_id":1,"excerpt":"availability was 98.5 percent"},{"source_id":2,"excerpt":"service experienced 17 minutes of downtime"}],sources,fetched,2)==[1,2]
    with pytest.raises(AssertionError): registry._validate_evidence([],sources,fetched,1)
    with pytest.raises(AssertionError): registry._validate_evidence([{"source_id":1,"excerpt":"availability was 98.5 percent"},{"source_id":1,"excerpt":"availability was 98.5 percent"}],sources,fetched,2)
    with pytest.raises(AssertionError): registry._validate_evidence([{"source_id":3,"excerpt":"x"}],sources,fetched,1)
    with pytest.raises(AssertionError): registry._validate_evidence([{"source_id":1,"excerpt":"service experienced 17 minutes of downtime"}],sources,fetched,1)
    with pytest.raises(AssertionError): registry._validate_evidence([{"source_id":1,"excerpt":""}],sources,fetched,1)
    with pytest.raises(AssertionError): registry._validate_evidence([{"source_id":1,"excerpt":"availability"}],sources,{1:"UNAVAILABLE"},1)
    with pytest.raises(AssertionError): registry._validate_evidence([{"source_id":1,"excerpt":"fabricated"}],sources,fetched,1)
