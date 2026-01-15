# Phase 2C: Cross-Country Spillovers - SKIPPED

**Decision Date:** 2026-01-13
**Status:** Deferred to V3.2

---

## Why Skipped

### Data Requirements Not Met

Phase 2C requires **bilateral data** (country-to-country flows):

| Required | Available | Gap |
|----------|-----------|-----|
| Bilateral trade flows (A→B exports) | Aggregate trade per country | Need CEPII BACI data |
| Bilateral migration stocks | Net migration per country | Need UN Migrant Stock data |
| Pairwise policy similarity | Per-country democracy scores | Need to compute similarity matrix |

### Cost-Benefit Analysis

| Approach | Data Sourcing | Compute Time | User Value |
|----------|---------------|--------------|------------|
| **Real Bilateral** | 10-20 hours manual | 35+ hours | 100% |
| **Regional Proxy** | 0 hours | 30 min | 70% |

**Decision:** Use regional proxy approach for V3.1, defer real bilateral to V3.2.

---

## Alternative: Regional Spillover Proxies

Added to Phase 3A instead:

```python
REGIONAL_SPILLOVER = {
    'sub_saharan_africa': {
        'dominant_economy': 'ZAF',  # South Africa
        'regional_leaders': ['NGA', 'KEN', 'ZAF'],
        'spillover_strength': 0.25
    },
    'east_asia_pacific': {
        'dominant_economy': 'CHN',
        'regional_leaders': ['CHN', 'JPN', 'KOR'],
        'spillover_strength': 0.45
    },
    # ... 11 regions total
}
```

### What This Enables

| User Question | V3.1 Answer |
|---------------|-------------|
| "If USA changes policy, does it affect others?" | Yes - shows regional spillover estimate |
| "Which countries are most influential?" | Yes - regional leaders flagged |
| "How does my country affect neighbors?" | Yes - simple regional coefficient |
| "Exact effect on Rwanda from USA policy?" | No - deferred to V3.2 |

---

## V3.2 Roadmap (If User Demand)

If users request precise bilateral effects after MVP launch:

1. **Data Sourcing (~13 hours)**
   - CEPII BACI bilateral trade: 5 hours
   - UN bilateral migration stocks: 3 hours
   - Data cleaning/alignment: 5 hours

2. **Computation (~35 hours)**
   - Trade channel regressions
   - Migration channel regressions
   - Policy diffusion estimation

3. **Integration (~10 hours)**
   - API endpoints
   - Frontend visualization

**Total V3.2 investment:** ~58 hours

---

## Impact on V3.1 Timeline

| Original Plan | Revised Plan |
|---------------|--------------|
| Phase 2C: 4.5 hours compute | SKIPPED |
| Phase 2C: 10-20 hours data sourcing | SKIPPED |
| Phase 3A: 6 hours | Phase 3A: 6.5 hours (+spillover proxies) |

**Net savings:** ~18+ hours
