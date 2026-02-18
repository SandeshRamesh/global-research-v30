"""
V3.1 Temporal Simulation

Multi-year simulation with:
- Year-specific graph loading for each projection year
- Lag-aware propagation
- Dynamic income classification tracking
- Non-linear effects
- Optional ensemble uncertainty
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Literal
from collections import defaultdict
import numpy as np

from .graph_loader_v31 import load_temporal_graph, build_adjacency_v31
from .income_classifier import get_country_classification, get_stratum_for_country
from .regional_spillovers import compute_regional_spillover, get_region_info
from .propagation_v31 import (
    propagate_intervention_v31,
    propagate_intervention_ensemble,
    compute_effects,
    get_top_effects,
    apply_saturation
)
from .simulation_runner_v31 import load_baseline_values

# Project paths
V31_ROOT = Path(__file__).parent.parent
DATA_DIR = V31_ROOT / "data"

# Constants
MIN_YEAR = 1990
MAX_YEAR = 2024

# Type definitions
ViewType = Literal['country', 'stratified', 'unified']


def propagate_temporal_v31(
    country: str,
    intervention: Optional[Dict[str, float]] = None,
    baseline_values: Dict[str, float] = None,
    base_year: int = 2024,
    horizon_years: int = 10,
    view_type: ViewType = 'country',
    p_value_threshold: float = 0.05,
    use_nonlinear: bool = True,
    use_dynamic_graphs: bool = True,
    dampening_factor: float = 0.5,
    max_percent_change: float = 100.0,
    interventions_by_year: Optional[Dict[int, Dict[str, float]]] = None
) -> dict:
    """
    Propagate intervention across multiple years using year-specific graphs.

    Key difference from instant simulation: loads a new graph for each
    projection year, accounting for evolving causal relationships.

    Supports staggered interventions: different indicators can be intervened
    at different years via interventions_by_year.

    Args:
        country: Country name
        intervention: {indicator: absolute_delta} — all applied at base_year (legacy)
        baseline_values: {indicator: baseline_value}
        base_year: Starting year (intervention year)
        horizon_years: Years to project forward
        view_type: Graph view type
        p_value_threshold: Edge significance filter
        use_nonlinear: Use marginal effects
        use_dynamic_graphs: Load year-specific graph for each year
        dampening_factor: Effect dampening
        max_percent_change: Maximum change cap
        interventions_by_year: {year: {indicator: absolute_delta}} — staggered interventions

    Returns:
        Dict with:
        - timeline: {year: {indicator: value}}
        - deltas: {year: {indicator: delta_from_baseline}}
        - graphs_used: {year: view_type_used}
        - converged_years: List of years that converged
    """
    timeline = {}
    deltas_timeline = {}
    graphs_used = {}
    converged_years = []

    # Build interventions_by_year from legacy param if not provided
    if interventions_by_year is None:
        interventions_by_year = {}
        if intervention:
            interventions_by_year[base_year] = intervention

    # Initialize year 0 (base year)
    current_values = dict(baseline_values)
    current_deltas = defaultdict(float)

    # Apply interventions scheduled for the base year
    if base_year in interventions_by_year:
        for indicator, delta in interventions_by_year[base_year].items():
            if indicator not in baseline_values:
                continue
            base = baseline_values[indicator]
            new_val = base + delta
            saturated = apply_saturation(indicator, new_val, base)
            current_values[indicator] = saturated
            current_deltas[indicator] = saturated - base

    timeline[base_year] = dict(current_values)
    deltas_timeline[base_year] = dict(current_deltas)

    # Propagate year by year
    for year_offset in range(1, horizon_years + 1):
        actual_year = base_year + year_offset

        # Clamp to data range
        graph_year = min(MAX_YEAR, actual_year)

        # Load graph for this year
        if use_dynamic_graphs:
            graph = load_temporal_graph(
                country=country,
                year=graph_year,
                view_type=view_type,
                p_value_threshold=p_value_threshold
            )
        else:
            # Use base year graph for all years (V3.0 style)
            graph = load_temporal_graph(
                country=country,
                year=base_year,
                view_type=view_type,
                p_value_threshold=p_value_threshold
            )

        if graph is None:
            # Use previous year's values if no graph
            timeline[actual_year] = dict(current_values)
            deltas_timeline[actual_year] = dict(current_deltas)
            graphs_used[actual_year] = 'none'
            continue

        graphs_used[actual_year] = graph.get('view_used', view_type)

        # Build adjacency for this year
        adjacency = build_adjacency_v31(graph)

        # Inject any staggered interventions scheduled for this year
        if actual_year in interventions_by_year:
            for indicator, delta in interventions_by_year[actual_year].items():
                if indicator not in baseline_values:
                    continue
                base = baseline_values[indicator]
                new_val = base + delta
                saturated = apply_saturation(indicator, new_val, base)
                current_values[indicator] = saturated
                current_deltas[indicator] = saturated - base

        # Compute effects for this year based on lagged changes
        new_deltas = defaultdict(float, current_deltas)
        changed_this_year = set()

        # For each edge, check if source effect from (year - lag) should apply
        for source, edges in adjacency.items():
            for edge in edges:
                target = edge.get('target')
                lag = edge.get('lag', 1)  # Default lag of 1 year

                # Check if we're at the right year for this lagged effect
                source_year = actual_year - lag
                if source_year < base_year:
                    continue  # Lag hasn't elapsed yet

                # Get source delta from the lagged year
                source_delta = deltas_timeline.get(source_year, {}).get(source, 0)
                if source_delta == 0:
                    continue

                # Get effect (use marginal effects if non-linear)
                if use_nonlinear and edge.get('marginal_effects'):
                    # Simple: use p50 marginal effect
                    effect = edge['marginal_effects'].get('p50', edge.get('beta', 0))
                else:
                    effect = edge.get('beta', 0)

                # Compute propagated effect
                propagated = effect * source_delta * dampening_factor

                # Accumulate
                if target in baseline_values:
                    new_deltas[target] += propagated
                    changed_this_year.add(target)

        # Apply saturation and update current values
        converged = True
        for indicator in new_deltas:
            if indicator not in baseline_values:
                continue

            base = baseline_values[indicator]
            proposed_delta = new_deltas[indicator]

            # Clamp
            max_delta = abs(base) * (max_percent_change / 100)
            clamped_delta = np.clip(proposed_delta, -max_delta, max_delta)

            new_val = base + clamped_delta
            saturated = apply_saturation(indicator, new_val, base)
            actual_delta = saturated - base

            # Check for significant change
            old_delta = current_deltas.get(indicator, 0)
            if abs(actual_delta - old_delta) > 0.001:
                converged = False

            current_values[indicator] = saturated
            current_deltas[indicator] = actual_delta

        if converged:
            converged_years.append(actual_year)

        timeline[actual_year] = dict(current_values)
        deltas_timeline[actual_year] = dict(current_deltas)

    return {
        'timeline': timeline,
        'deltas': deltas_timeline,
        'graphs_used': graphs_used,
        'converged_years': converged_years
    }


def run_temporal_simulation_v31(
    country: str,
    interventions: List[dict],
    base_year: int,
    horizon_years: int = 10,
    view_type: ViewType = 'country',
    p_value_threshold: float = 0.05,
    use_nonlinear: bool = True,
    use_dynamic_graphs: bool = True,
    n_ensemble_runs: int = 0,
    include_spillovers: bool = True,
    top_n_effects: int = 20,
    panel_path: Optional[Path] = None
) -> dict:
    """
    Run temporal simulation with year-by-year graphs.

    Args:
        country: Country name
        interventions: List of {indicator: str, change_percent: float}
        base_year: Intervention year
        horizon_years: Years to project forward (1-30)
        view_type: Graph view type
        p_value_threshold: Edge significance filter
        use_nonlinear: Use marginal effects when available
        use_dynamic_graphs: Load year-specific graph for each projection year
        n_ensemble_runs: 0 = point estimate, >0 = bootstrap ensemble
        include_spillovers: Include regional spillover effects
        top_n_effects: Number of top effects per year
        panel_path: Override panel data path

    Returns:
        Dict with timeline, effects per year, metadata
    """
    try:
        # Load baseline
        baseline, year_used, percentiles = load_baseline_values(country, base_year, panel_path)
        if not baseline:
            return {
                'status': 'error',
                'message': f"No baseline data for '{country}' in year {base_year}"
            }

        # Convert interventions — group by year for staggered support
        interventions_by_year: Dict[int, Dict[str, float]] = defaultdict(dict)
        intervention_details = []

        for intv in interventions:
            indicator = intv.get('indicator')
            change_percent = intv.get('change_percent', 0)
            intervention_year = intv.get('intervention_year', base_year)

            if indicator not in baseline:
                intervention_details.append({
                    'indicator': indicator,
                    'change_percent': change_percent,
                    'intervention_year': intervention_year,
                    'status': 'skipped',
                    'reason': 'not_in_baseline'
                })
                continue

            base_val = baseline[indicator]
            delta = base_val * (change_percent / 100)
            interventions_by_year[intervention_year][indicator] = delta

            intervention_details.append({
                'indicator': indicator,
                'baseline': base_val,
                'change_percent': change_percent,
                'change_absolute': delta,
                'intervention_year': intervention_year,
                'status': 'applied'
            })

        if not interventions_by_year:
            return {
                'status': 'error',
                'message': 'No valid interventions'
            }

        # Compute effective base_year and horizon from staggered interventions
        all_intervention_years = list(interventions_by_year.keys())
        effective_base_year = min(all_intervention_years)
        max_intervention_year = max(all_intervention_years)
        # Ensure horizon covers from earliest intervention to latest + horizon_years
        effective_horizon = max(horizon_years, (max_intervention_year - effective_base_year) + horizon_years)

        # Run temporal propagation
        result = propagate_temporal_v31(
            country=country,
            baseline_values=baseline,
            base_year=effective_base_year,
            horizon_years=effective_horizon,
            view_type=view_type,
            p_value_threshold=p_value_threshold,
            use_nonlinear=use_nonlinear,
            use_dynamic_graphs=use_dynamic_graphs,
            interventions_by_year=dict(interventions_by_year)
        )

        # Compute effects for each year
        effects_by_year = {}
        affected_per_year = {}

        for year, values in result['timeline'].items():
            year_effects = compute_effects(baseline, values)
            top = get_top_effects(year_effects, top_n=top_n_effects)
            effects_by_year[year] = top
            affected_per_year[year] = len([e for e in year_effects.values()
                                            if e.get('absolute_change', 0) != 0])

        # Track income classification evolution
        income_evolution = {}
        for year in result['timeline'].keys():
            income_evolution[year] = get_country_classification(country, year) or {}

        # Build response
        response = {
            'status': 'success',
            'country': country,
            'base_year': year_used or effective_base_year,
            'horizon_years': effective_horizon,
            'view_type': view_type,
            'interventions': intervention_details,
            'timeline': result['timeline'],
            'effects': effects_by_year,
            'affected_per_year': affected_per_year,
            'graphs_used': result['graphs_used'],
            'income_classification_evolution': income_evolution,
            'metadata': {
                'p_value_threshold': p_value_threshold,
                'use_nonlinear': use_nonlinear,
                'use_dynamic_graphs': use_dynamic_graphs,
                'converged_years': result['converged_years'],
                'timestamp': datetime.now().isoformat()
            }
        }

        # Add spillovers for final year if enabled
        if include_spillovers:
            final_year = effective_base_year + effective_horizon
            final_effects = effects_by_year.get(final_year, {})
            abs_effects = {ind: eff.get('absolute_change', 0) for ind, eff in final_effects.items()}
            spillovers = compute_regional_spillover(country, abs_effects)

            response['spillovers'] = {
                'final_year': final_year,
                'regional': spillovers.get('regional', {}),
                'global': spillovers.get('global', {}),
                'region_info': get_region_info(country)
            }

        return response

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def compute_temporal_effects(
    baseline_values: Dict[str, float],
    timeline: Dict[int, Dict[str, float]],
    top_n: int = 20
) -> Dict[int, Dict[str, dict]]:
    """
    Compute top effects for each year in timeline.

    Returns:
        {year: {indicator: {baseline, value, absolute_change, percent_change}}}
    """
    result = {}
    for year, values in timeline.items():
        effects = compute_effects(baseline_values, values)
        result[year] = get_top_effects(effects, top_n=top_n)
    return result


def format_temporal_results(result: dict) -> str:
    """Format temporal simulation results for CLI display."""
    if result.get('status') == 'error':
        return f"Error: {result.get('message', 'Unknown error')}"

    lines = [
        f"\n{'='*60}",
        f"Temporal Simulation: {result['country']}",
        f"Base Year: {result['base_year']} → {result['base_year'] + result['horizon_years']}",
        f"{'='*60}",
        f"\nInterventions:"
    ]

    for intv in result.get('interventions', []):
        status = "✓" if intv['status'] == 'applied' else "✗"
        lines.append(f"  {status} {intv['indicator']}: {intv.get('change_percent', 0):+.1f}%")

    lines.append(f"\nEffects over time:")
    for year in sorted(result.get('affected_per_year', {}).keys()):
        affected = result['affected_per_year'][year]
        view = result.get('graphs_used', {}).get(year, 'N/A')
        lines.append(f"  Year {year}: {affected} indicators affected (graph: {view})")

    # Show final year top effects
    final_year = result['base_year'] + result['horizon_years']
    if final_year in result.get('effects', {}):
        lines.append(f"\nTop Effects at Year {final_year}:")
        for ind, eff in list(result['effects'][final_year].items())[:5]:
            pct = eff.get('percent_change', 0)
            lines.append(f"  {ind}: {pct:+.2f}%")

    if result.get('spillovers', {}).get('region_info'):
        ri = result['spillovers']['region_info']
        lines.append(f"\nRegional Spillovers ({ri.get('name')}):")
        lines.append(f"  Strength: {ri.get('spillover_strength', 0):.0%}")

    lines.append(f"\n{'='*60}\n")
    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def _run_tests():
    """Run basic tests."""
    print("\nRunning temporal simulation tests...")
    print("-" * 40)

    from .graph_loader_v31 import get_available_countries

    countries = get_available_countries()
    print(f"  Available countries: {len(countries)}")

    if countries:
        test_country = 'Australia' if 'Australia' in countries else countries[0]
        result = run_temporal_simulation_v31(
            country=test_country,
            interventions=[{'indicator': 'v2pehealth', 'change_percent': 20}],
            base_year=2015,
            horizon_years=5,
            use_dynamic_graphs=True
        )

        if result['status'] == 'success':
            print(f"  Temporal simulation test: SUCCESS")
            print(f"    Country: {result['country']}")
            print(f"    Years: {result['base_year']} to {result['base_year'] + result['horizon_years']}")
            print(f"    Graphs used: {list(result['graphs_used'].values())[:3]}...")
        else:
            print(f"  Temporal simulation test: {result.get('message', 'FAILED')}")

    print("-" * 40)
    print("Temporal simulation tests completed\n")


if __name__ == "__main__":
    _run_tests()
