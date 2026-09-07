# Covenant architecture

The Registry seals operator, clauses, public HTTPS sources, schedule, definition hash, status, and audit findings. Its semantic boundary is intended to use `gl.vm.run_nondet_unsafe`: a leader fetches bounded source text and classifies each clause; validators independently refetch, re-evaluate, and verify excerpts. `INCONCLUSIVE` and `UNAVAILABLE` never slash. The Vault holds GEN and applies only Registry-finalized, exact-once slash decisions to the sealed recovery address.
