# Phase 3B: Development Clusters - Results

**Completed:** 2026-01-14
**Runtime:** < 1 minute (178 countries + 35 unified years)
**Status:** ✅ COMPLETE

---

## Overview

Phase 3B identifies **Development Clusters** - groups of indicators that are tightly connected through causal pathways. This replaces the original "Feedback Loop" concept because the causal graph is a DAG (Directed Acyclic Graph) by design, meaning traditional A↔B feedback loops don't exist.

**What we compute instead:** Using Louvain community detection, we find "indicator ecosystems" - groups of variables that tend to influence each other through causal chains.

---

## Output Statistics

| Metric | Value |
|--------|-------|
| **Total files** | **213** |
| Country files | 178 |
| Unified (global) files | 35 (1990-2024) |
| Clusters per country | 3-23 (mean: 16) |
| Nodes per cluster | 5-341 |

### File Locations

```
data/v3_1_development_clusters/
├── countries/              # 178 files
│   ├── Afghanistan_clusters.json
│   ├── Albania_clusters.json
│   └── ... (178 countries)
└── unified/                # 35 files
    ├── 1990_clusters.json
    ├── 1991_clusters.json
    └── ... (35 years)
```

---

## Methodology

### Why Not "Feedback Loops"?

The V2.1 causal graph is a **DAG** - edges only go one direction. This is standard in causal inference:
- If Education → Income exists, Income → Education does NOT exist
- Even indirect paths (A→B→C→...→A) don't form cycles

**However**, feedback in the real world is captured through **temporal lags**:
```
Education_t → Income_{t+5} (5-year lag)
Income_t → Education_{t+3} (3-year lag)
```

This IS feedback - just temporally separated, not structurally cyclic.

### What We Compute Instead

**Development Clusters** use community detection (Louvain algorithm) to find groups of indicators that are densely connected through causal edges:

```python
# Algorithm
1. Load temporal graph (significant edges only, p < 0.05)
2. Treat as undirected graph (ignore edge direction for clustering)
3. Weight edges by |beta| (causal strength)
4. Run Louvain community detection
5. Classify clusters by domain composition
```

### Cluster Classification

Clusters are named by their dominant domain(s):
- **Single domain**: "Economic Cluster" (>25% of nodes from one domain)
- **Dual domain**: "Economic-Environment Cluster" (top two domains >15% each)
- **Mixed**: "Mixed Cluster" (no dominant domain)

---

## Output Schema

### Country File

```json
{
  "country": "Japan",
  "year_analyzed": 2024,
  "n_years_available": 26,
  "clusters": [
    {
      "cluster_id": 0,
      "name": "Governance-Economic Cluster",
      "size": 203,
      "domain_composition": {
        "Governance": 58,
        "Economic": 53,
        "Education": 36,
        "Environment": 26,
        "Development": 18,
        "Health": 10,
        "Security": 2
      },
      "primary_domain": "Governance",
      "secondary_domain": "Economic",
      "density": 0.0401,
      "mean_edge_strength": 0.668,
      "n_internal_edges": 822,
      "sample_indicators": [
        "Income per Person (US$)",
        "Foreign currency reserves in months of imports",
        "Manufactured Goods as Share of Total Exports"
      ]
    }
  ],
  "summary": {
    "n_clusters": 18,
    "total_nodes_in_clusters": 1144,
    "largest_cluster": 203,
    "mean_cluster_size": 63.6,
    "clusters_by_domain": {"Governance": 3, "Economic": 5, "Health": 1, ...}
  },
  "metadata": {
    "computation_time_sec": 0.05,
    "graph_file": "2024_graph.json",
    "n_edges_in_graph": 3895
  },
  "provenance": {
    "computation_date": "2026-01-14T08:35:28.758474",
    "code_version": "v3.1.0",
    "algorithm": "louvain",
    "p_value_threshold": 0.05,
    "min_cluster_size": 5
  }
}
```

### Unified (Global) File

```json
{
  "source": "unified",
  "year": 2024,
  "clusters": [
    {
      "cluster_id": 0,
      "name": "Governance-Economic Cluster",
      "size": 341,
      "domain_composition": {
        "Governance": 108,
        "Economic": 89,
        "Education": 57,
        "Environment": 44,
        "Development": 23,
        "Health": 13,
        "Security": 7
      },
      "primary_domain": "Governance",
      "secondary_domain": "Economic",
      "density": 0.01,
      "mean_edge_strength": 0.3746,
      "n_internal_edges": 577,
      "sample_indicators": [
        "Number of baby boy deaths under age 1",
        "Foreign Social Media Advertising",
        "Individual Income Comparison Index"
      ]
    }
  ],
  "summary": {
    "n_clusters": 14,
    "total_nodes_in_clusters": 1926,
    "largest_cluster": 341,
    "mean_cluster_size": 137.6,
    "clusters_by_domain": {"Governance": 4, "Education": 4, "Development": 2, ...}
  },
  "metadata": {
    "computation_time_sec": 0.11,
    "n_edges_in_graph": 7368
  },
  "provenance": {
    "computation_date": "2026-01-14T08:35:33.099317",
    "code_version": "v3.1.0",
    "algorithm": "louvain",
    "p_value_threshold": 0.05,
    "min_cluster_size": 5
  }
}
```

**Key differences between country and unified:**
- Country files have `country` and `year_analyzed`; unified files have `source: "unified"` and `year`
- Country files include `n_years_available` and `graph_file` in metadata
- Unified files typically have larger clusters (pooled across all countries)

---

## Sample Results

### Countries with Most Clusters

| Country | Clusters | Largest Cluster |
|---------|----------|-----------------|
| Venezuela | 23 | - |
| United States | 22 | - |
| Sudan | 22 | - |
| New Zealand | 21 | - |
| Vietnam | 21 | - |
| Australia | 21 | - |

### Countries with Fewest Clusters

| Country | Clusters | Notes |
|---------|----------|-------|
| South Yemen | 3 | Limited data (historical) |
| German Democratic Republic | 5 | Historical entity |
| The Gambia | 8 | Small country |
| Somaliland | 8 | Limited recognition |

### Unified (Global) Cluster Trend

| Year | Clusters | Notes |
|------|----------|-------|
| 1990 | 16 | Early data |
| 2000 | 18 | - |
| 2010 | 16 | - |
| 2020 | 17 | - |
| 2024 | 14 | Most recent |

The number of clusters is relatively stable over time (14-24), suggesting consistent causal structure.

---

## Common Cluster Types

Based on analysis of unified 2024:

| Cluster Type | Typical Size | Example Indicators |
|--------------|--------------|-------------------|
| **Governance-Economic** | 150-340 | Democracy indices, GDP, trade policy |
| **Education-Economic** | 100-300 | School enrollment, income, literacy |
| **Health-Education** | 80-200 | Life expectancy, child mortality, education years |
| **Economic-Environment** | 100-260 | GDP, emissions, energy use |
| **Development-Economic** | 80-150 | Infrastructure, urbanization, income |

---

## Interpretation Guide

### What Clusters Mean

**High density cluster** (density > 0.05): Indicators that strongly co-vary
- Changes in one indicator likely propagate to others
- Policy interventions have broad effects within cluster

**Cross-domain cluster** (e.g., "Economic-Environment"):
- Shows interconnection between development dimensions
- Illustrates why siloed policy approaches often fail

### Frontend Use Cases

1. **Highlight clusters on hover**: Show which indicators belong to same ecosystem
2. **Cluster-based filtering**: "Show me all indicators in the Human Capital cluster"
3. **Policy impact preview**: "If I change this indicator, which others are likely affected?"

---

## Validation Notes

### Verified

- [x] All 178 countries processed
- [x] All 35 unified years processed
- [x] No empty files
- [x] Cluster sizes ≥ 5 (minimum threshold)
- [x] Domain classification consistent with node metadata

### Known Limitations

1. **Ignores edge direction**: Clusters are based on undirected connectivity
2. **Single year per country**: Uses most recent year only (2024 for most)
3. **No temporal tracking**: Doesn't show how clusters evolve over time

### Future Enhancements (V3.2)

- Track cluster evolution over time
- Compute cluster "stability" (how consistent across years)
- Identify "bridge" indicators connecting multiple clusters

---

## Technical Details

### Algorithm: Louvain Community Detection

```python
from networkx.algorithms import community

# Build undirected graph
G = nx.Graph()
for edge in graph['edges']:
    if edge['p_value'] < 0.05:
        G.add_edge(edge['source'], edge['target'], weight=abs(edge['beta']))

# Detect communities
communities = community.louvain_communities(G, weight='weight', seed=42)
```

### Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_value_threshold` | 0.05 | Standard significance |
| `min_cluster_size` | 5 | Avoid noise clusters |
| `edge_weight` | abs(beta) | Strength of causal relationship |
| `seed` | 42 | Reproducibility |

---

## Files

| File | Description |
|------|-------------|
| `scripts/phase3_analysis/detect_development_clusters.py` | Computation script |
| `data/v3_1_development_clusters/countries/*.json` | 178 country files |
| `data/v3_1_development_clusters/unified/*.json` | 35 unified files |

---

## CLI Usage

```bash
# Test run
python scripts/phase3_analysis/detect_development_clusters.py --test --test-n 10

# Full production
python scripts/phase3_analysis/detect_development_clusters.py --jobs 8

# Resume interrupted run
python scripts/phase3_analysis/detect_development_clusters.py --resume
```

---

## Next Steps

- [x] Phase 3B: Development Clusters ← COMPLETE
- [x] Phase 3A: Feedback Loops ← COMPLETE (0 loops found)
- [x] Phase 4: Full validation suite ← CERTIFIED
