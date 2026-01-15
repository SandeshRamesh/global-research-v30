# Phase 2B: Temporal Causal Graphs - Results

**Completed:** 2026-01-14
**Runtime:** 87.8 minutes total (unified + stratified + country)
**Status:** ✅ COMPLETE
**Total Files:** 4,768

---

## Overview

Phase 2B computed causal edge beta coefficients over time, tracking how causal relationships between indicators strengthen or weaken across years. Each file contains the V2.1 edge set (7,368 edges) with regression betas, confidence intervals, optimal lags, and p-values.

**Scope:**
- **Country-specific:** Per-country graphs (1999-2024)
- **Unified (Global):** Pooled all-country graphs (1990-2024)

---

## Final Statistics

### Country-Specific Graphs

| Metric | Value |
|--------|-------|
| Total files generated | **4,628** |
| Countries | 178 |
| Year range | 1999-2024 (26 years) |
| Runtime | ~47 minutes |
| Cores used | 4 |

### Unified (Global) Graphs

| Metric | Value |
|--------|-------|
| Total files generated | **35** |
| Year range | 1990-2024 (35 years) |
| Samples per year | 846 (1990) → 29,867 (2024) |
| Edge coverage | 52% (1990) → 100% (2024) |
| Runtime | 11.6 minutes |

### Combined Totals

| Metric | Value |
|--------|-------|
| **Total files** | **4,663** |
| Causal edges per file | Up to 7,368 |

---

## Output Structure

```
data/v3_1_temporal_graphs/
├── unified/                    # 35 files (1990-2024)
│   ├── 1990_graph.json
│   ├── 1991_graph.json
│   └── ... (35 files)
└── countries/                  # 4,628 files (1999-2024)
    ├── Afghanistan/
    │   ├── 1999_graph.json
    │   └── ... (up to 2024)
    ├── Albania/
    └── ... (178 countries)
```

### Why Country-Specific Starts at 1999?

Early years (1990-1998) lack sufficient per-country data points. The MIN_SAMPLES=10 requirement filters these out. Unified graphs work for all years because pooling ~800+ countries provides enough samples.

---

## File Schema

### Country-Specific

```json
{
  "country": "United States",
  "year": 2020,
  "edges": [
    {
      "source": "education_spending",
      "target": "gdp_per_capita",
      "beta": 0.38,
      "ci_lower": 0.31,
      "ci_upper": 0.45,
      "std": 0.04,
      "p_value": 0.0001,
      "lag": 3,
      "r_squared": 0.42,
      "n_samples": 31,
      "n_bootstrap": 100,
      "relationship_type": "linear"
    }
  ],
  "metadata": {
    "n_edges_computed": 4500,
    "n_edges_skipped": 2868,
    "n_edges_total": 7368,
    "coverage": 0.61,
    "mean_beta": 0.186,
    "std_beta": 0.45,
    "median_p_value": 0.08,
    "significant_edges_p05": 3200,
    "significant_edges_p01": 1200,
    "mean_lag": 1.8,
    "lag_distribution": {"0": 2000, "1": 1500, "2": 600, "3": 300, "4": 80, "5": 20},
    "nonlinear_edges": 0,
    "dag_validated": true,
    "dag_cycles": [],
    "n_samples": 31,
    "year_range": [1990, 2020],
    "computation_time_sec": 8.5
  },
  "saturation_thresholds": {...},
  "provenance": {...}
}
```

### Unified (additional field)

```json
{
  "country": "unified",
  "year": 2020,
  "metadata": {
    "n_countries": 893,  // Additional field for unified
    ...
  }
}
```

---

## Academic Specification

### Features Implemented

| Feature | Description | Status |
|---------|-------------|--------|
| **Lag Selection** | Test lags 0-5 years, select by best R² | ✅ |
| **Bootstrap CIs** | 100 iterations for confidence intervals | ✅ |
| **P-values** | T-statistic based significance | ✅ |
| **DAG Validation** | Cycle detection via NetworkX | ✅ |
| **Non-linearity** | Quadratic vs linear R² comparison (top 500 edges) | ✅ |
| **Saturation Thresholds** | Pre-defined limits for simulation | ✅ |
| **Numba Optimization** | JIT-compiled bootstrap loop | ✅ |
| **Unified Graphs** | Global pooled data across all countries | ✅ |

### Not Implemented

| Feature | Reason |
|---------|--------|
| Chow Test / Structural Breaks | Explicitly excluded per user request |

---

## Edge Statistics

### Unified 2024 (example)

| Metric | Value |
|--------|-------|
| Edges computed | 7,368 (100%) |
| Significant (p<0.05) | 7,181 (97%) |
| Mean lag | 1.3 years |
| Samples | 29,867 |

### Country-Specific (samples)

| Country/Year | Edges | Significant (p<0.05) | Coverage |
|--------------|-------|----------------------|----------|
| Japan 2020 | 3,735 | 2,718 (73%) | 51% |
| UK 2002 | 1,142 | 863 (76%) | 15% |
| Unified 2020 | 7,368 | 7,181 (97%) | 100% |

---

## Configuration

```python
MIN_YEAR = 1990
MAX_YEAR = 2024
BOOTSTRAP_SAMPLES = 100
MIN_SAMPLES = 10
MAX_LAG = 5
N_JOBS = 4
TOP_N_NONLINEAR = 500
NONLINEARITY_THRESHOLD = 0.10
```

---

## Validation Checklist

- [x] All files valid JSON (NumpyEncoder handles int64/float64)
- [x] Bootstrap CIs present (ci_lower < beta < ci_upper)
- [x] DAG validation in all files (dag_validated: true)
- [x] Lag distribution logged (0-5 years)
- [x] P-values computed for significance testing
- [x] Provenance logged in each file
- [x] Unified output matches documentation schema
- [x] Saturation fields present when applicable
- [ ] Temporal smoothness check (pending Phase 4)

---

## Files

| File | Description |
|------|-------------|
| `data/v3_1_temporal_graphs/unified/*.json` | 35 unified graph files |
| `data/v3_1_temporal_graphs/countries/**/*.json` | 4,628 country graph files |
| `scripts/phase2_compute/compute_temporal_graphs.py` | Computation script |

---

## CLI Usage

```bash
# Country-specific production
python scripts/phase2_compute/compute_temporal_graphs.py

# Unified production
python scripts/phase2_compute/compute_temporal_graphs.py --unified

# Test modes
python scripts/phase2_compute/compute_temporal_graphs.py --test
python scripts/phase2_compute/compute_temporal_graphs.py --unified-test

# Resume interrupted run
python scripts/phase2_compute/compute_temporal_graphs.py --resume
```

---

## Next Steps

- [x] Phase 2B: Temporal Causal Graphs ← COMPLETE
- [ ] Phase 2C: Cross-Country Spillovers
- [ ] Phase 3: Regional Aggregates
- [ ] Phase 4: Validation suite
