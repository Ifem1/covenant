# v0.2.18
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

@gl.contract_interface
class RegistryInterface:
    class View:
        def get_covenant(self,covenant_id): ...
        def get_audit(self,audit_id): ...
        def get_canonical_vault(self): ...
    class Write:
        def mark_funded(self,covenant_id): ...
        def mark_audit_settled(self,audit_id): ...

class CovenantVault(gl.Contract):
    registry: Address
    bonds: TreeMap[u256,u256]
    principal: TreeMap[u256,u256]
    consumed_slash_bps: TreeMap[u256,u32]
    slashed_amount: TreeMap[u256,u256]
    settled: TreeMap[str,bool]
    slash_state: TreeMap[str,u32]
    reserved_slash_amount: TreeMap[str,u256]
    pending_slash_count: TreeMap[u256,u32]
    close_state: TreeMap[u256,u32]
    def __init__(self, registry: Address): self.registry = registry
    @gl.public.view
    def get_bond(self,covenant_id: u256) -> u256: return self.bonds.get(covenant_id,u256(0))
    @gl.public.write.payable
    def deposit_bond(self,covenant_id):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); assert RegistryInterface(self.registry).view().get_canonical_vault()==gl.message.contract_address and c.operator==gl.message.sender_address and c.status=='DRAFT' and gl.message.value>=c.minimum_bond; assert self.bonds.get(covenant_id,u256(0))==0; self.principal[covenant_id]=gl.message.value; self.bonds[covenant_id]=gl.message.value; RegistryInterface(self.registry).emit(on='finalized').mark_funded(covenant_id)
    @gl.public.write
    def reconcile_funding(self,covenant_id: u256):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); assert self.bonds.get(covenant_id,u256(0))>0; RegistryInterface(self.registry).emit(on='finalized').mark_funded(covenant_id) if c.status=='DRAFT' else None
    @gl.public.write
    def apply_slash(self,covenant_id,audit_id):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); a=RegistryInterface(self.registry).view().get_audit(audit_id); state=self.slash_state.get(audit_id,u32(0)); assert a.covenant_id==covenant_id and a.outcome=='BREACH' and state<3
        if state==0:
            used=self.consumed_slash_bps.get(covenant_id,u32(0))+a.slash_bps; assert used<=10000; p=self.principal.get(covenant_id,u256(0)); target=p*used//10000; old=self.slashed_amount.get(covenant_id,u256(0)); amount=target-old; self.consumed_slash_bps[covenant_id]=used; self.slashed_amount[covenant_id]=target; self.bonds[covenant_id]-=amount; self.reserved_slash_amount[audit_id]=amount; self.pending_slash_count[covenant_id]=self.pending_slash_count.get(covenant_id,u32(0))+1; self.slash_state[audit_id]=u32(1); RegistryInterface(self.registry).emit(on='finalized').mark_audit_settled(audit_id); return
        if not a.settled: RegistryInterface(self.registry).emit(on='finalized').mark_audit_settled(audit_id); return
        amount=self.reserved_slash_amount.get(audit_id,u256(0)); self.slash_state[audit_id]=u32(3); self.pending_slash_count[covenant_id]-=1
        if amount>0: _Recipient(c.recovery).emit_transfer(value=amount)
    @gl.public.write
    def close_and_refund(self,covenant_id):
        c=RegistryInterface(self.registry).view().get_covenant(covenant_id); assert c.operator==gl.message.sender_address and c.status=='EXPIRED' and self.pending_slash_count.get(covenant_id,u32(0))==0; state=self.close_state.get(covenant_id,u32(0));
        if state==0: self.close_state[covenant_id]=u32(1); RegistryInterface(self.registry).emit(on='finalized').mark_closed(covenant_id); return
        assert RegistryInterface(self.registry).view().get_covenant(covenant_id).status=='CLOSED'; amount=self.bonds.get(covenant_id,u256(0)); self.bonds[covenant_id]=u256(0); self.close_state[covenant_id]=u32(2)
        if amount>0: _Recipient(c.operator).emit_transfer(value=amount)

@gl.evm.contract_interface
class _Recipient:
    class View: pass
    class Write: pass
