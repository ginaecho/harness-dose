"""Proof harness for OpenHarness.

* ``metrics``    — confusion matrix, precision/recall/F1
* ``agent_sim``  — a scripted agent that *executes the skills*, compliantly or not
* ``l1_conformance`` — does the layer MEASURE correctly? (offline, labeled corpus)
* ``l2_ablation``    — does enforcing it IMPROVE outcomes? (A/B with gating)

Run ``python -m benchmark.l1_conformance`` and ``python -m benchmark.l2_ablation``
(or ``make prove``) to regenerate the reports under ``benchmark/reports/``.
"""
