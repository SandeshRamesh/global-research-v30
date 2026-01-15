# Phase 2A: Temporal SHAP - Results

**Status:** ✅ COMPLETE
**Completion Date:** 2026-01-15
**Runtime:** 6.38 hours on AWS c7i.8xlarge (8 workers)
**Total Files:** 4,767

---

## Critical Validation Findings (2026-01-14)

### Methodology Validation Tests

Three validation tests were run to assess the robustness of the SHAP methodology:

| Test | Finding | Implication |
|------|---------|-------------|
| **Failure Bias** | 0% failure rate across all income groups | ✅ No systematic bias |
| **Aggregation Sensitivity** | r=0.453 (arithmetic vs geometric) | ⚠️ HIGH sensitivity |
| **Cross-Income Heterogeneity** | r=0.25-0.30 between income groups | 🚨 CRITICAL |

### Key Finding: Cross-Income Heterogeneity

**Cross-group SHAP correlations:**
- Low+Lower-mid vs Upper-middle: **r = 0.290**
- Low+Lower-mid vs High: **r = 0.248**
- Upper-middle vs High: **r = 0.275**

**Interpretation:** Fundamentally different indicators matter for countries at different development stages. A unified model averaging all countries masks these critical differences.

### Architecture Decision: Stratified Views

Based on validation findings, the architecture now includes:

| View | Description | Justification |
|------|-------------|---------------|
| **Unified** | Global average (all countries pooled) | Baseline comparison |
| **Developing** | Low + Lower-middle income | r=0.25-0.30 vs others |
| **Emerging** | Upper-middle income | Transition economies |
| **Advanced** | High income | Mature economies |

---

## Dynamic Income Classification

Countries are classified dynamically using World Bank historical GNI per capita thresholds (not fixed 2024 status).

**Mapping to 3-tier groups:**
```
Low income           → Developing
Lower middle income  → Developing
Upper middle income  → Emerging
High income          → Advanced
```

**Group sizes by decade:**
| Year | Developing | Emerging | Advanced | Unknown |
|------|------------|----------|----------|---------|
| 1990 | 115 | 24 | 32 | 7 |
| 2000 | 104 | 36 | 31 | 7 |
| 2010 | 88 | 42 | 41 | 7 |
| 2020 | 75 | 43 | 53 | 7 |
| 2024 | 71 | 45 | 55 | 7 |

**Notable Transitions (76 countries):**
- China: Developing → Emerging (2010)
- Korea: Emerging → Advanced (1992)
- Poland: Developing → Emerging (1995) → Advanced (2008)
- India: Low income → Lower-middle (still Developing, 2007)

**Data Source:** `data/metadata/income_classifications.json`

---

## Methodology Revision (2026-01-14)

### Problem with Previous Approach

**Old approach (9 models + averaging):**
```
Train 9 domain models → Average SHAP across domains = "Unified"
```

**Issues:**
- Averaging implies all domains equally important
- Doesn't directly answer "what matters to quality of life?"
- Indicator important in 1 domain gets diluted (0.8/9 = 0.09)
- **NEW:** Cross-income correlation of only r=0.25-0.30 means pooling all countries masks critical heterogeneity

### New Approach: Single Model SHAP

```python
# Create composite target from ALL 9 domain aggregates
For each (entity, year):  # entity = unified/stratified/country
  1. For EACH of 9 domains:
     - Get ALL indicators from V2.1 hierarchy
     - Normalize to [0, 1]
     - INVERT negative outcomes (mortality, inequality, disease)
     - domain_agg = mean(normalized indicators)

  2. Composite target:
     quality_of_life = mean(health_agg, education_agg, ..., environment_agg)

  3. Train SINGLE model: X = all indicators → y = quality_of_life
  4. SHAP directly answers: "How important is this to OVERALL quality of life?"
```

---

## Data Quality Fixes

### Country List (Fixed)
- **178 canonical countries** from `v3_1_temporal_graphs/countries/`
- Full names ("Afghanistan", "United States") not ISO codes ("AFG", "USA")
- Filtered out regional aggregates ("Arab World", "OECD", etc.)
- Filtered out numeric codes (UN M49 region codes)

### V2.1 Outcome Domains (9 total)
1. Health & Longevity (143 indicators)
2. Education & Knowledge (491 indicators)
3. Income & Living Standards (191 indicators)
4. Equality & Fairness (126 indicators)
5. Safety & Security (36 indicators)
6. Governance & Democracy (357 indicators)
7. Infrastructure & Access (229 indicators)
8. Employment & Work (96 indicators)
9. Environment & Sustainability (300 indicators)

---

## Computation Plan

### File Estimates

| Component | Count | Years | Files |
|-----------|-------|-------|-------|
| Unified (global average) | 1 | 35 | 35 |
| Stratified (Developing) | 1 | 35 | 35 |
| Stratified (Emerging) | 1 | 35 | 35 |
| Stratified (Advanced) | 1 | 35 | 35 |
| Countries | 178 | ~30 | ~5,340 |
| **Total** | - | - | **~5,480** |

### Script
| Script | Purpose |
|--------|---------|
| `compute_stratified_shap.py` | Single model → quality_of_life (unified + stratified + countries) |

---

## Output Structure

```
v3_1_temporal_shap/
├── unified/
│   └── quality_of_life/           # 35 files (1990-2024)
│       ├── 1990_shap.json
│       └── ...
├── stratified/
│   ├── developing/                # 35 files
│   │   ├── 1990_shap.json
│   │   └── ...
│   ├── emerging/                  # 35 files
│   └── advanced/                  # 35 files
└── countries/                      # 178 countries
    └── {CountryName}/
        └── quality_of_life/       # ~30 files per country
```

**Key Difference:** Stratified views use dynamic classification - a country like China appears in "Developing" pre-2010 and "Emerging" 2010+.

---

## File Schemas (Stratified Architecture)

### Unified/Stratified View Schema

```json
{
  "stratum": "unified",
  "stratum_name": "Global Average (All Countries)",
  "target": "quality_of_life",
  "target_name": "Quality of Life",
  "year": 1997,
  "stratification": {
    "countries_in_stratum": ["Afghanistan", "Albania", ...],
    "n_countries": 178,
    "note": "Global average - may not reflect context-specific patterns."
  },
  "shap_importance": {
    "indicator_id": {
      "mean": 0.0137,
      "std": 0.0264,
      "ci_lower": 0.0,
      "ci_upper": 0.0936
    }
  },
  "metadata": {
    "n_samples": 1424,
    "n_countries": 178,
    "n_indicators": 2232,
    "n_bootstrap": 100,
    "r2_mean": 0.988,
    "r2_std": 0.003,
    "year_range": [1990, 1997],
    "computation_time_sec": 772.86
  },
  "data_quality": {
    "mean_ci_width": 0.018
  },
  "provenance": {
    "computation_date": "2026-01-14T17:10:19",
    "code_version": "v3.1.0",
    "model": "LightGBM",
    "hyperparameters": {
      "n_estimators": 100,
      "max_depth": 5,
      "learning_rate": 0.1,
      "subsample": 0.8,
      "colsample_bytree": 0.8,
      "min_child_samples": 10,
      "random_state": 42
    }
  }
}
```

### Income-Stratified View Schema

For `stratified/developing/`, `stratified/emerging/`, `stratified/advanced/`:

```json
{
  "stratum": "developing",
  "stratum_name": "Developing Countries",
  "target": "quality_of_life",
  "target_name": "Quality of Life",
  "year": 2010,
  "stratification": {
    "wb_groups_included": ["Low income", "Lower middle income"],
    "classification_source": "World Bank GNI per capita",
    "countries_in_stratum": ["Afghanistan", "Bangladesh", ...],
    "n_countries": 88,
    "dynamic_note": "Country membership changes by year based on income classification"
  },
  "shap_importance": { ... },
  "metadata": { ... },
  "data_quality": { ... },
  "provenance": { ... }
}
```

### Country-Specific Schema

For `countries/{CountryName}/quality_of_life/`:

```json
{
  "country": "United States",
  "target": "quality_of_life",
  "target_name": "Quality of Life",
  "year": 2020,
  "shap_importance": {
    "indicator_id": {
      "mean": 0.34,
      "std": 0.04,
      "ci_lower": 0.28,
      "ci_upper": 0.41
    }
  },
  "metadata": {
    "n_samples": 31,
    "n_indicators": 2590,
    "n_bootstrap": 100,
    "r2_mean": 0.95,
    "r2_std": 0.02,
    "year_range": [1990, 2020],
    "computation_time_sec": 2.9
  },
  "data_quality": {
    "mean_ci_width": 0.15
  },
  "provenance": { ... }
}
```

---

## Configuration

```python
MIN_YEAR = 1995
MAX_YEAR = 2024
MIN_SAMPLES = 10
MIN_INDICATORS = 20
BOOTSTRAP_SAMPLES = 100
N_JOBS = 12  # parallel cores (thermal safety)
CANONICAL_COUNTRIES = 178  # from temporal graphs

# LightGBM hyperparameters
MODEL_PARAMS = {
    'n_estimators': 100,
    'max_depth': 5,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'random_state': 42,
    'verbose': -1,
    'n_jobs': 1  # inner parallelism disabled
}
```

---

## Validation Checklist

- [ ] All files valid JSON
- [ ] Bootstrap CIs present (ci_lower ≤ mean ≤ ci_upper)
- [ ] SHAP values in [0, 1] range
- [ ] Stratum fields match (unified/developing/emerging/advanced)
- [ ] Country names are full names (not ISO codes)
- [ ] R² values reasonable (>0.8 for unified, >0.7 for country)
- [ ] Temporal smoothness (max year-over-year change < 0.3)
- [ ] n_bootstrap = 100 for all views

---

## Status

| Step | Status |
|------|--------|
| Old outputs archived | ✅ Complete |
| **Methodology validation** | ✅ Complete |
| - Failure bias test | ✅ 0% failure across income groups |
| - Aggregation sensitivity | ✅ r=0.453 (arithmetic vs geometric) |
| - Cross-income heterogeneity | ✅ r=0.25-0.30 → stratified architecture |
| **Income classification data** | ✅ Complete |
| - World Bank GNI data fetched | ✅ 1990-2024 |
| - 178 countries mapped | ✅ 76 transitions tracked |
| - Saved to metadata | ✅ `income_classifications.json` |
| Documentation updated | ✅ Complete |
| **compute_stratified_shap.py** | ✅ Written (8 workers) |
| **Production run** | ✅ COMPLETE (6.38 hours) |
| - Unified (global) | ✅ 35/35 |
| - Stratified (3 groups) | ✅ 104/105 |
| - Countries (178) | ✅ 4,628 files (74% coverage) |
| **Total output files** | ✅ 4,767 |

---

## Validation Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/validation/quick_validation.py` | Fast 3-test validation | Console output |
| `scripts/validation/test_stratification.py` | Compare income vs geographic | Console output |
| `scripts/data/fetch_income_classifications.py` | Fetch WB income data | `income_classifications.json` |
