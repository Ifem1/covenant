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
    assert registry._validate_evidence([1],"grounded",sources,1)==[1]
    with pytest.raises(AssertionError): registry._validate_evidence([],"grounded",sources,1)
    with pytest.raises(AssertionError): registry._validate_evidence([1,1],"grounded",sources,2)
    with pytest.raises(AssertionError): registry._validate_evidence([3],"grounded",sources,1)
    with pytest.raises(AssertionError): registry._validate_evidence([1],"",sources,1)
