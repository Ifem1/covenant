# v0.2.18
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

@gl.contract_interface
class RegistryInterface:
    class View:
        def get_covenant(self,covenant_id): ...
        def get_audit(self,audit_id): ...
    class Write:
        def mark_funded(self,covenant_id): ...
        def mark_audit_settled(self,audit_id): ...

class CovenantVault(gl.Contract):
    registry: Address
    bonds: TreeMap[u256,u256]
    settled: TreeMap[str,bool]
    def __init__(self,registry): self.registry=registry; self.bonds=TreeMap(); self.settled=TreeMap()
    @gl.public.view
    def get_bond(self,covenant_id: u256) -> u256: return self.bonds.get(covenant_id,u256(0))
    @gl.public.write.payable
    def deposit_bond(self,covenant_id):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); assert c.operator==gl.message.sender_address and c.status=='DRAFT' and gl.message.value>=c.minimum_bond; assert self.bonds.get(covenant_id,u256(0))==0; self.bonds[covenant_id]=gl.message.value; RegistryInterface(self.registry).emit(on='finalized').mark_funded(covenant_id)
    @gl.public.write
    def apply_slash(self,covenant_id,audit_id):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); a=RegistryInterface(self.registry).view().get_audit(audit_id); assert a.covenant_id==covenant_id and a.outcome=='BREACH' and not a.settled and not self.settled.get(audit_id,False); amount=self.bonds[covenant_id]*a.slash_bps//10000; self.bonds[covenant_id]-=amount; self.settled[audit_id]=True; RegistryInterface(self.registry).emit(on='finalized').mark_audit_settled(audit_id); _Recipient(c.recovery).emit_transfer(value=amount)
    @gl.public.write
    def close_and_refund(self,covenant_id):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); assert c.operator==gl.message.sender_address and c.status=='EXPIRED'; amount=self.bonds.get(covenant_id,u256(0)); self.bonds[covenant_id]=u256(0); _Recipient(c.operator).emit_transfer(value=amount)

@gl.evm.contract_interface
class _Recipient:
    class View: pass
    class Write: pass
