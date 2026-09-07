# v0.2.18
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class CovenantVault(gl.Contract):
    def __init__(self, registry): self.registry=registry; self.bonds=TreeMap(); self.slashed=TreeMap()
    @gl.public.write
    def deposit_bond(self,covenant_id):
        c=self.registry.get_covenant(covenant_id); assert c['operator']==gl.message.sender and c['status']=='DRAFT'; assert gl.message.value>=c['minimum_bond']; self.bonds[covenant_id]=self.bonds.get(covenant_id,u256(0))+gl.message.value; c['status']='FUNDED'
    @gl.public.view
    def get_bond(self,covenant_id): return self.bonds.get(covenant_id,u256(0))
    @gl.public.write
    def apply_slash(self,covenant_id,audit_id):
        assert not self.slashed.get(audit_id,False); c=self.registry.get_covenant(covenant_id); a=self.registry.audits[audit_id]; assert a['outcome']=='BREACH'; amount=self.bonds[covenant_id]*a['slash_bps']//10000; self.bonds[covenant_id]-=amount; self.slashed[audit_id]=True; gl.message.send(c['recovery'],amount)
    @gl.public.write
    def close_and_refund(self,covenant_id):
        c=self.registry.get_covenant(covenant_id); assert c['operator']==gl.message.sender and c['status'] in ['EXPIRED','CLOSED','GOOD_STANDING']; amount=self.bonds[covenant_id]; self.bonds[covenant_id]=u256(0); c['status']='CLOSED'; gl.message.send(c['operator'],amount)
