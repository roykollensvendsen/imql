# Authoring guide (prescriptive path)

Use the schema to **design a new incentive mechanism** from scratch.

1. Copy the template:
   ```bash
   cp templates/blank-instance.yaml instances/sample/my-design.yaml   # or anywhere
   ```
2. Keep `instance_kind: authored`. Leave `provenance` out — it is not required for authored specs.
3. Fill `subnet.name` and a one-paragraph `task.summary`. Set `subnet.owner_repo: null`.
4. Work top-down through the schema as a **design checklist**:
   - **What do miners submit?** → `task.submission_format`.
   - **What is measured?** → `scoring_signals[]`. Be explicit about `direction` and relative `weight`.
   - **Against what truth?** → `ground_truth_sources[]`. This is where most mechanisms live or die;
     name the `kind` and `trust_model` honestly.
   - **How do scores become weights?** → `aggregation` (+ `decay_rate`, `min_weight_floor`, burn).
   - **How often / how committed?** → `weight_setting`.
   - **How is it gamed, and what stops that?** → `anti_gaming[]`. If you can't fill this, the design
     is not finished.
   - **Is there a ladder/tournament/multi-track?** → `sub_competitions`.
   - **Is state carried across rounds?** → `per_miner_state`.
5. Validate continuously:
   ```bash
   python tooling/validate.py instances/sample/my-design.yaml
   ```
6. If a real design idea has no field, first try an enum `other` + `*_other`; if it's genuinely
   structural and recurring, that's **schema stress** — raise it for a versioned schema change
   (see `schema/CHANGELOG.md` governance) rather than abusing `extensions`.

The discipline of filling every required block tends to surface under-specified mechanisms early:
an empty `anti_gaming` or a hand-wavy `ground_truth_sources` is a design smell, not a schema gap.
