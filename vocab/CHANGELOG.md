# Metric ontology changelog

The ontology is the canonicalization layer for the bespoke metric tail. Governed like the schema: a
new family / specific / alias needs **≥2× recurrence + a CHANGELOG entry + a VERSION bump +
re-running coverage**. Instances keep the raw metric string immutable; resolution happens at read time
(`imml_core.resolve_metric`), so canonicalization is non-destructive and reversible.

## 0.1.0 — initial ontology

Authored families-first from the corpus census of the 75 distinct bespoke (`metric_kind: other`)
metric strings. 15 families, 51 aliases. Resolves **51/75 (68%)** of bespoke leaves, lifting
IMML structural-expressibility from 87.0% → **95.8%** (coverage gate PASS).

Families: classification_quality, content_quality, cross_subnet_aggregate, cryptographic_auth,
data_freshness, financial_pnl, generative_reward, hardware_authenticity, market_outcome,
model_architecture, predictive_contribution, probabilistic_forecast, risk_adjusted_ratio,
throughput_latency, volume. (All ⊆ the schema's `metric_family` enum.)

The **24 unmatched** are the irreducible long tail — opaque external weight feeds, undocumented
mechanisms, and one-off stake/burn/allocation metrics. Listed in `reports/vocab-candidates.md`. None
recurs ≥2× across subnets, so none qualifies for promotion yet — consistent with the corpus finding
that the metric tail is flat. They remain `extern` leaves (hand-written `score()` in generation).
