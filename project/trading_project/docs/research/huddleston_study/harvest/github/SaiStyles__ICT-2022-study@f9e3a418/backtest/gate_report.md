# Does each gate earn its place?

`dev`, 2,969 sessions. Ledger n = 128. Holdout SEALED.

ep24 [17:41]: the setup that never formed `is the proof, the evidence
that the model has validity`. **Both sides use the same 2R target**, so
the only thing separating them is the gate itself.

**Accepted: 171 trades at -0.185R (win 27%).** A gate earns its place only if what it
threw away did WORSE than that. `z` is accepted minus refused; the bar
is |z| > 3.0 (DECISIONS.md 24).

| gate | refused | their expectancy | win | **z** | verdict |
|---|---|---|---|---|---|
| g2_liquidity_taken | 3,571 | -0.029R | 32% | **-1.54** | **threw away BETTER trades** |
| g3_displacement | 635 | +0.111R | 37% | **-2.60** | **threw away BETTER trades** |
| g5_gap_in_discount | 252 | -0.089R | 31% | **-0.73** | **threw away BETTER trades** |
| g7_ote | 117 | -0.179R | 27% | **-0.04** | **threw away BETTER trades** |
