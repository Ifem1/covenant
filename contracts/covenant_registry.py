# v0.2.18
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class CovenantRegistry(gl.Contract):
    def __init__(self): self.covenants=TreeMap(); self.audits=TreeMap(); self.next_id=u256(1)
    @gl.public.view
    def get_covenant(self, covenant_id): return self.covenants.get(covenant_id)
    @gl.public.view
    def is_audit_due(self, covenant_id):
        c=self.covenants.get(covenant_id); return c is not None and c['status'] in ['ACTIVE','GOOD_STANDING'] and gl.get_block_timestamp() >= c['next_audit']
    @gl.public.write
    def create_covenant(self, service_name, description, recovery, minimum_bond, interval, clauses, sources, demo=False):
        assert len(clauses)>0 and len(clauses)<=12 and len(sources)>=2 and len(sources)<=5 and sum(x['slash_bps'] for x in clauses)<=10000
        cid=self.next_id; self.next_id+=1
        self.covenants[cid]={'operator':gl.message.sender,'service':service_name,'description':description,'recovery':recovery,'minimum_bond':minimum_bond,'interval':interval,'next_audit':gl.get_block_timestamp()+interval,'clauses':clauses,'sources':sources,'status':'DRAFT','definition_hash':sha256(str((service_name,description,clauses,sources)).encode()).hex(),'breach_count':0,'remaining_slash_bps':10000}
        return cid
    @gl.public.write
    def activate(self,covenant_id):
        c=self.covenants[covenant_id]; assert c['operator']==gl.message.sender and c['status']=='FUNDED'; c['status']='ACTIVE'
    @gl.public.write
    def record_audit(self,covenant_id, findings, interval_start, interval_end):
        c=self.covenants[covenant_id]; assert self.is_audit_due(covenant_id) and len(findings)==len(c['clauses'])
        assert interval_end > interval_start and interval_end <= gl.get_block_timestamp()
        assert c['status'] != 'UNDER_REVIEW'
        assert all(f['clause_id'] == i+1 for i,f in enumerate(findings))
        # Semantic boundary: source text is hostile data, never instructions.
        # Leader and validators must independently fetch and agree on these fields
        # before this write is submitted by the application.
        breached=[f for f in findings if f['finding']=='BREACHED']; unresolved=any(f['finding'] in ['INCONCLUSIVE','UNAVAILABLE'] for f in findings)
        outcome='BREACH' if breached else ('INCONCLUSIVE' if unresolved else 'CLEAN')
        aid=str((covenant_id,interval_start,interval_end)); assert self.audits.get(aid) is None
        slash=sum(c['clauses'][f['clause_id']-1]['slash_bps'] for f in breached); assert slash <= c['remaining_slash_bps']
        self.audits[aid]={'outcome':outcome,'findings':findings,'slash_bps':slash,'definition_hash':c['definition_hash']}; c['remaining_slash_bps']-=slash; c['status']='BREACHED' if outcome=='BREACH' else ('GOOD_STANDING' if outcome=='CLEAN' else 'UNDER_REVIEW'); c['next_audit']=interval_end+c['interval']; c['latest_audit']=aid; c['breach_count']+=len(breached); return aid
