# Offer baselines

- template_top_affinity: n=150, gate_pass=100%, mean affinity=0.405
- random_template: n=150, gate_pass=100%, mean affinity=0.118
- generic: n=150, gate_pass=0%, mean affinity=0.405

sanity: generic must be gated to 0;
template_top_affinity affinity must beat random_template
