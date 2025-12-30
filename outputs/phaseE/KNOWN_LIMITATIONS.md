# V3.0 Simulation System: Known Limitations

## Performance Metrics (Historical Validation)

| Metric | Result | Target | Status | Interpretation |
|--------|--------|--------|--------|----------------|
| **r²** | 0.091 | >0.5 | FAIL | Explains 9% of variance (high noise) |
| **Direction accuracy** | 29% | >70% | FAIL | Worse than coin flip (50%) |
| **Top-10 overlap** | 57.9% | >50% | PASS | Correctly identifies most-affected indicators |
| **Magnitude ratio** | 0.99 | ~1.0 | PASS | Calibrated magnitudes |
| **CI coverage** | 22% | 95% | FAIL | Uncertainty 4x wider than CIs suggest |

## Validation Test Results

| Test | Status | Notes |
|------|--------|-------|
| Holdout validation | PASS | Holdout r²=0.146 vs in-sample r²=0.091 (no overfitting) |
| Stress tests | PASS | Extreme interventions saturate correctly |
| Reproducibility | PASS | Deterministic results across runs |
| Negative interventions | PARTIAL | Australia passed, India failed (84% sign mismatch) |

---

## Validated Use Cases

**The system IS reliable for:**

1. **Scenario comparison** - "Policy A affects GDP 12% more than Policy B"
2. **Indicator identification** - "These 10 indicators will be most affected"
3. **Mechanism exploration** - "Education affects GDP through literacy and productivity"
4. **Relative magnitudes** - "This effect is 2x larger than that effect"

---

## Unsupported Use Cases

**The system is NOT reliable for:**

1. **Absolute forecasting** - "GDP will be $45,320 in 2025" (r² too low)
2. **Direction prediction** - "This will increase GDP" (only 29% accuracy)
3. **Point estimates** - "Life expectancy will increase by exactly 2.3 years" (wide CIs)
4. **Single-indicator predictions** - Some indicators have high variance

---

## Why Low Direction Accuracy?

Our analysis shows **temporal/contextual factors dominate**:

- Same country (Nigeria) shows 0% direction accuracy in 1999, 74% in 2018
- External shocks (recessions, wars, pandemics) not modeled
- Unobserved confounders change across time periods
- Short time series (35 years) → large standard errors

**Implication:** Direction depends more on context than causal structure.

---

## Why Some Indicators Fail Negative Intervention Test?

For some indicators (e.g., SLE.1T2.M in India), positive and negative interventions
produce effects with the **same sign** in 84% of downstream indicators.

**Possible causes:**
- Edge weights have incorrect signs (correlational, not causal)
- Non-linear relationships not captured by linear propagation
- Mediator effects dominate direct effects

**Implication:** Use symmetric interventions (A vs B comparison) rather than
absolute predictions.

---

## Recommendations for Users

1. **Always compare scenarios** (A vs B), never predict absolutes
2. **Use wide confidence intervals** (multiply published CIs by 4)
3. **Focus on top-10 affected indicators** (57.9% overlap accuracy)
4. **Consult domain experts** before policy decisions
5. **Treat as exploratory tool**, not decision oracle
6. **Cross-validate critical findings** with external data/models

---

## API Usage Guidelines

### DO:
```json
// Compare two scenarios
{
  "scenario_a": {"interventions": [{"indicator": "health_spending", "change_percent": 10}]},
  "scenario_b": {"interventions": [{"indicator": "education_spending", "change_percent": 10}]}
}
// Compare: "Which affects life expectancy more?"
```

### DON'T:
```json
// Predict absolute outcomes
{
  "interventions": [{"indicator": "health_spending", "change_percent": 10}]
}
// Expect: "Life expectancy will be exactly 72.3 years"
```

---

## Calibration Recommendations

When using simulation results:

| What You Get | How to Interpret |
|--------------|------------------|
| Effect magnitude X% | True effect is X% × 0.25 (calibration factor applied) |
| Confidence interval [a, b] | True interval is approximately [a×4, b×4] |
| Top-10 affected indicators | 58% likely to be correct |
| Direction of effect | 29% likely to be correct (use with caution) |

---

## Technical Notes

### Model Specifications
- **Edge estimation**: Country-specific Lasso regression on V2.0 panel data
- **Lag estimation**: Granger causality tests (1-5 year lags)
- **Propagation**: Temporal simulation with 0.5 dampening factor
- **Saturation**: Logistic bounds to prevent unrealistic values
- **Calibration**: 0.25x magnitude scaling (empirically derived)

### Data Limitations
- Time series: 1990-2023 (35 years)
- Countries: 217 with variable data coverage
- Indicators: ~2,500 with 30-90% country coverage
- Missing data: Imputed using country/year medians

### Known Data Issues
- Pre-1990 data sparse for many developing countries
- Some governance indicators change methodology over time
- COVID-19 (2020-2022) creates structural break

---

## Planned Improvements (V3.1+)

1. **External shock database** - Filter crisis years automatically
2. **Longer time series** - Incorporate pre-1990 data where available
3. **Bayesian hierarchical modeling** - Better uncertainty quantification
4. **Cross-country spillovers** - Trade and migration effects
5. **Domain-specific sub-models** - Specialized health, education modules
6. **Sign constraints** - Domain knowledge to fix edge signs

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2025-12-29 | Initial release with documented limitations |

---

## Contact

- Technical questions: support@argonanalytics.com
- Methodology concerns: research@argonanalytics.com
- Bug reports: https://github.com/argonanalytics/v3-simulation/issues
