# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class DirectControl(gl.Contract):
    owner: Address
    def __init__(self, owner: Address): self.owner=owner
    @gl.public.view
    def get_owner(self) -> Address: return self.owner
    @gl.public.write
    def run_probe(self) -> str:
        def leader(): return 'probe-ok'
        def validator(result): return isinstance(result, gl.vm.Return) and result.calldata == 'probe-ok'
        return gl.vm.run_nondet(leader, validator)
