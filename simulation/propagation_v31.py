"""
V3.1 Intervention Propagation

Propagates intervention effects through causal graph with:
- Non-linear propagation using marginal_effects at source percentile
- Ensemble uncertainty via bootstrap resampling of edge weights
- Saturation functions to prevent unrealistic values
"""

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Literal
import numpy as np

# Add V3.0 saturation functions to path
V30_ROOT = Path(__file__).parent.parent.parent / "v3.0"
sys.path.insert(0, str(V30_ROOT / "scripts" / "phaseB" / "B1_saturation"))

try:
    from saturation_functions import apply_saturation
except ImportError:
    # Fallback: inline basic saturation
    def apply_saturation(indicator: str, value: float, baseline: float) -> float:
        """Basic saturation fallback."""
        indicator_lower = indicator.lower()
        # Hard cap for rates
        if any(p in indicator_lower for p in ['rate', 'literacy', 'enrollment', 'mortality']):
            return float(np.clip(value, 0, 100))
        # Hard cap for indices
        if any(p in indicator_lower for p in ['v2x_', 'index', 'score']):
            return float(np.clip(value, 0, 1))
        return value


def get_marginal_effect(
    edge: dict,
    source_value: float,
    percentile: float
) -> float:
    """
    Get appropriate marginal effect based on source value's percentile.

    For non-linear edges (V3.1 v2):
    - Interpolate between p25, p50, p75 marginal effects
    - This captures diminishing returns, thresholds, etc.

    For linear edges: Use beta directly.

    Args:
        edge: Edge dict with beta and optionally marginal_effects
        source_value: Current value of source indicator
        percentile: Source value's percentile in distribution (0-1)

    Returns:
        Marginal effect to use for propagation
    """
    marginal_effects = edge.get('marginal_effects')
    relationship_type = edge.get('relationship_type', 'linear')

    # If no marginal effects or linear relationship, use beta
    if marginal_effects is None or relationship_type == 'linear':
        return edge.get('beta', 0)

    # Extract percentile-specific effects
    p25 = marginal_effects.get('p25', edge.get('beta', 0))
    p50 = marginal_effects.get('p50', edge.get('beta', 0))
    p75 = marginal_effects.get('p75', edge.get('beta', 0))

    # Linear interpolation based on source percentile
    if percentile <= 0.25:
        return p25
    elif percentile <= 0.50:
        # Interpolate between p25 and p50
        t = (percentile - 0.25) / 0.25
        return p25 + t * (p50 - p25)
    elif percentile <= 0.75:
        # Interpolate between p50 and p75
        t = (percentile - 0.50) / 0.25
        return p50 + t * (p75 - p50)
    else:
        return p75


def resample_edge_weights(
    adjacency: Dict[str, List[dict]],
    rng: np.random.Generator,
    uncertainty_multiplier: float = 3.0
) -> Dict[str, List[dict]]:
    """
    Bootstrap resample edge weights for ensemble simulation.

    Uses edge.std: new_beta ~ Normal(beta, std * uncertainty_multiplier)

    The uncertainty_multiplier accounts for:
    - Unmodeled external factors
    - Propagation uncertainty
    - Model specification uncertainty

    Empirically calibrated: 1x gives ~29% coverage, 3x gives ~80-90% coverage.

    Args:
        adjacency: Original adjacency dict
        rng: Numpy random generator
        uncertainty_multiplier: Scaling factor for std (default 3.0)

    Returns:
        New adjacency with resampled betas
    """
    resampled = {}

    for source, edges in adjacency.items():
        resampled_edges = []
        for edge in edges:
            beta = edge.get('beta', 0)
            std = edge.get('std', 0)

            # Resample beta from normal distribution
            if std > 0:
                resampled_beta = rng.normal(beta, std * uncertainty_multiplier)
            else:
                resampled_beta = beta

            # Copy edge with new beta
            new_edge = edge.copy()
            new_edge['beta'] = resampled_beta
            new_edge['original_beta'] = beta

            # Also resample marginal effects if present
            if edge.get('marginal_effects'):
                me = edge['marginal_effects']
                new_me = {}
                for key in ['p25', 'p50', 'p75']:
                    if key in me:
                        # Assume similar relative uncertainty
                        ratio = resampled_beta / beta if beta != 0 else 1.0
                        new_me[key] = me[key] * ratio
                new_edge['marginal_effects'] = new_me

            resampled_edges.append(new_edge)
        resampled[source] = resampled_edges

    return resampled


def propagate_intervention_v31(
    adjacency: Dict[str, List[dict]],
    intervention: Dict[str, float],
    baseline_values: Dict[str, float],
    indicator_percentiles: Optional[Dict[str, float]] = None,
    max_iterations: int = 10,
    convergence_threshold: float = 0.001,
    dampening_factor: float = 0.5,
    max_percent_change: float = 100.0,
    use_nonlinear: bool = True
) -> dict:
    """
    Propagate intervention through causal graph.

    Single-run propagation with optional non-linear effects.

    Args:
        adjacency: Graph adjacency dict from build_adjacency_v31()
        intervention: {indicator: absolute_delta} to apply
        baseline_values: {indicator: current_value}
        indicator_percentiles: {indicator: percentile} for non-linear marginal effects
        max_iterations: Maximum propagation iterations
        convergence_threshold: Stop when max change < this
        dampening_factor: Scale down cascading effects (0.5 = 50% dampening)
        max_percent_change: Cap maximum % change from baseline
        use_nonlinear: Use marginal_effects when available

    Returns:
        Dict with:
        - values: Final indicator values
        - deltas: Change from baseline for each indicator
        - lower_bound: Lower CI estimate (approx)
        - upper_bound: Upper CI estimate (approx)
        - iterations: Iterations until convergence
        - converged: Whether converged before max_iterations
    """
    # Initialize
    current_values = dict(baseline_values)
    cumulative_deltas = defaultdict(float)
    lower_bound = {}
    upper_bound = {}

    # Apply initial intervention
    changed_nodes = set()
    for indicator, delta in intervention.items():
        if indicator not in baseline_values:
            continue

        baseline = baseline_values[indicator]
        new_val = baseline + delta
        saturated = apply_saturation(indicator, new_val, baseline)

        current_values[indicator] = saturated
        cumulative_deltas[indicator] = saturated - baseline
        changed_nodes.add(indicator)

        # Initialize CI bounds
        lower_bound[indicator] = saturated
        upper_bound[indicator] = saturated

    # Propagate iteratively
    for iteration in range(max_iterations):
        new_changes = defaultdict(float)
        newly_changed = set()

        # For each changed source, propagate to targets
        for source in changed_nodes:
            source_delta = cumulative_deltas[source]
            if source_delta == 0:
                continue

            # Get outgoing edges
            edges = adjacency.get(source, [])

            for edge in edges:
                target = edge.get('target')
                if target is None or target not in baseline_values:
                    continue

                # Determine effect to use
                if use_nonlinear and indicator_percentiles:
                    source_percentile = indicator_percentiles.get(source, 0.5)
                    effect = get_marginal_effect(edge, current_values.get(source, 0), source_percentile)
                else:
                    effect = edge.get('beta', 0)

                # Compute propagated effect with dampening
                propagated_effect = effect * source_delta * dampening_factor
                new_changes[target] += propagated_effect

        # Apply accumulated changes
        for target, total_effect in new_changes.items():
            baseline = baseline_values[target]
            current_delta = cumulative_deltas[target]
            proposed_delta = current_delta + total_effect

            # Clamp to max percent change
            max_delta = abs(baseline) * (max_percent_change / 100)
            clamped_delta = np.clip(proposed_delta, -max_delta, max_delta)

            # Compute new value
            new_val = baseline + clamped_delta
            saturated = apply_saturation(target, new_val, baseline)
            actual_delta = saturated - baseline

            # Check if significant change
            if abs(actual_delta - current_delta) > convergence_threshold:
                newly_changed.add(target)

            current_values[target] = saturated
            cumulative_deltas[target] = actual_delta

            # Update CI bounds (simple ±5% approximation)
            lower_bound[target] = min(lower_bound.get(target, saturated), saturated * 0.95)
            upper_bound[target] = max(upper_bound.get(target, saturated), saturated * 1.05)

        # Check convergence
        if not newly_changed:
            return {
                'values': dict(current_values),
                'deltas': dict(cumulative_deltas),
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'iterations': iteration + 1,
                'converged': True
            }

        changed_nodes = newly_changed

    # Max iterations reached
    return {
        'values': dict(current_values),
        'deltas': dict(cumulative_deltas),
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'iterations': max_iterations,
        'converged': False
    }


def propagate_intervention_ensemble(
    adjacency: Dict[str, List[dict]],
    intervention: Dict[str, float],
    baseline_values: Dict[str, float],
    indicator_percentiles: Optional[Dict[str, float]] = None,
    n_runs: int = 100,
    seed: int = 42,
    uncertainty_multiplier: float = 3.0,
    **propagation_kwargs
) -> dict:
    """
    Run ensemble simulation with bootstrap resampling for uncertainty.

    Runs N propagations with resampled edge weights, returns median + CI.

    Args:
        adjacency: Graph adjacency dict
        intervention: {indicator: absolute_delta}
        baseline_values: {indicator: current_value}
        indicator_percentiles: For non-linear propagation
        n_runs: Number of bootstrap iterations (default 100)
        seed: Random seed for reproducibility
        uncertainty_multiplier: Scaling for edge weight resampling
        **propagation_kwargs: Passed to propagate_intervention_v31()

    Returns:
        Dict with:
        - values: Median final values
        - deltas: Median changes from baseline
        - ci_lower: 2.5th percentile (95% CI lower)
        - ci_upper: 97.5th percentile (95% CI upper)
        - std: Standard deviation across runs
        - n_runs: Number of runs performed
        - converged_runs: Number of runs that converged
    """
    rng = np.random.default_rng(seed)

    # Collect results across runs
    all_values = defaultdict(list)
    all_deltas = defaultdict(list)
    converged_count = 0

    for _ in range(n_runs):
        # Resample edge weights
        resampled_adj = resample_edge_weights(adjacency, rng, uncertainty_multiplier)

        # Run propagation
        result = propagate_intervention_v31(
            resampled_adj,
            intervention,
            baseline_values,
            indicator_percentiles,
            **propagation_kwargs
        )

        if result['converged']:
            converged_count += 1

        # Collect values
        for indicator, value in result['values'].items():
            all_values[indicator].append(value)
        for indicator, delta in result['deltas'].items():
            all_deltas[indicator].append(delta)

    # Compute statistics
    median_values = {}
    median_deltas = {}
    ci_lower = {}
    ci_upper = {}
    std_values = {}

    for indicator in all_values:
        values = np.array(all_values[indicator])
        deltas = np.array(all_deltas[indicator])

        median_values[indicator] = float(np.median(values))
        median_deltas[indicator] = float(np.median(deltas))
        ci_lower[indicator] = float(np.percentile(values, 2.5))
        ci_upper[indicator] = float(np.percentile(values, 97.5))
        std_values[indicator] = float(np.std(deltas))

    return {
        'values': median_values,
        'deltas': median_deltas,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'std': std_values,
        'n_runs': n_runs,
        'converged_runs': converged_count,
        'convergence_rate': converged_count / n_runs
    }


def compute_effects(
    baseline_values: Dict[str, float],
    simulated_values: Dict[str, float],
    indicators: Optional[List[str]] = None
) -> Dict[str, dict]:
    """
    Compute effect details for each indicator.

    Args:
        baseline_values: Original values
        simulated_values: Values after intervention
        indicators: Optional list to filter

    Returns:
        {indicator: {baseline, simulated, absolute_change, percent_change}}
    """
    effects = {}

    target_indicators = indicators or list(simulated_values.keys())

    for indicator in target_indicators:
        baseline = baseline_values.get(indicator)
        simulated = simulated_values.get(indicator)

        if baseline is None or simulated is None:
            continue

        abs_change = simulated - baseline
        pct_change = (abs_change / baseline * 100) if baseline != 0 else 0

        effects[indicator] = {
            'baseline': baseline,
            'simulated': simulated,
            'absolute_change': abs_change,
            'percent_change': pct_change
        }

    return effects


def propagate_intervention_percentage(
    adjacency: Dict[str, List[dict]],
    intervention: Dict[str, float],
    use_nonlinear: bool = True,
    max_iterations: int = 100,
    convergence_threshold: float = 1e-6,
    dampening_factor: float = 0.5
) -> dict:
    """
    Propagate percentage changes through causal graph.

    No baseline values needed - works entirely in percentages.
    This is the FAST PATH for simulation that avoids loading 65MB panel data.

    Args:
        adjacency: Graph adjacency dict with beta coefficients
        intervention: {indicator_id: change_percent}
        use_nonlinear: Use marginal_effects when available
        max_iterations: Maximum propagation iterations
        convergence_threshold: Stop when max change < this
        dampening_factor: Scale down cascading effects (0.5 = 50% dampening)

    Returns:
        {
            'percent_changes': {indicator: percent_change},
            'iterations': int,
            'converged': bool
        }
    """
    # Initialize with intervention percentages
    percent_changes = dict(intervention)
    changed_nodes = set(intervention.keys())

    for iteration in range(max_iterations):
        new_changes = {}

        for source in changed_nodes:
            source_change_pct = percent_changes.get(source, 0)
            if source_change_pct == 0:
                continue

            # Get outgoing edges
            edges = adjacency.get(source, [])

            for edge in edges:
                target = edge.get('target')
                if target is None:
                    continue

                # Get effect coefficient
                beta = edge.get('beta', 0)

                # Non-linear: use marginal effects if available
                if use_nonlinear:
                    nonlinearity = edge.get('nonlinearity', {})
                    if nonlinearity.get('detected') and 'marginal_effects' in nonlinearity:
                        # Use median marginal effect (p50) for percentage propagation
                        beta = nonlinearity['marginal_effects'].get('p50', beta)

                # Propagate percentage through beta with dampening
                # If source changes by X%, target changes by X% * beta * dampening
                target_delta = source_change_pct * beta * dampening_factor

                if target in new_changes:
                    new_changes[target] += target_delta
                else:
                    new_changes[target] = target_delta

        # Check convergence
        if not new_changes:
            return {
                'percent_changes': percent_changes,
                'iterations': iteration + 1,
                'converged': True
            }

        max_update = max(abs(v) for v in new_changes.values())
        if max_update < convergence_threshold:
            return {
                'percent_changes': percent_changes,
                'iterations': iteration + 1,
                'converged': True
            }

        # Apply updates
        newly_changed = set()
        for target, delta in new_changes.items():
            old_val = percent_changes.get(target, 0)
            new_val = old_val + delta

            # Only track significant changes
            if abs(new_val - old_val) > convergence_threshold:
                newly_changed.add(target)

            percent_changes[target] = new_val

        changed_nodes = newly_changed

        if not changed_nodes:
            return {
                'percent_changes': percent_changes,
                'iterations': iteration + 1,
                'converged': True
            }

    return {
        'percent_changes': percent_changes,
        'iterations': max_iterations,
        'converged': False
    }


def get_top_percent_effects(
    percent_changes: Dict[str, float],
    top_n: int = 20
) -> Dict[str, dict]:
    """
    Get top N effects by percent change magnitude.

    Args:
        percent_changes: {indicator: percent_change}
        top_n: Number of top effects to return

    Returns:
        {indicator: {'percent_change': float}}
    """
    sorted_effects = sorted(
        percent_changes.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    return {
        ind: {'percent_change': pct}
        for ind, pct in sorted_effects[:top_n]
    }


def get_top_effects(
    effects: Dict[str, dict],
    top_n: int = 20,
    sort_by: Literal['absolute', 'percent'] = 'absolute'
) -> Dict[str, dict]:
    """
    Get top N effects by magnitude.

    Args:
        effects: Output from compute_effects()
        top_n: Number of top effects to return
        sort_by: Sort by 'absolute' or 'percent' change

    Returns:
        Top N effects dict
    """
    if sort_by == 'absolute':
        key_func = lambda x: abs(x[1].get('absolute_change', 0))
    else:
        key_func = lambda x: abs(x[1].get('percent_change', 0))

    sorted_effects = sorted(effects.items(), key=key_func, reverse=True)

    return dict(sorted_effects[:top_n])


# =============================================================================
# TESTS
# =============================================================================

def _run_tests():
    """Run basic tests."""
    print("\nRunning propagation tests...")
    print("-" * 40)

    # Test marginal effect extraction
    linear_edge = {'beta': 0.5, 'relationship_type': 'linear'}
    effect = get_marginal_effect(linear_edge, 100, 0.5)
    assert effect == 0.5
    print("  get_marginal_effect (linear): PASS")

    nonlinear_edge = {
        'beta': 0.5,
        'relationship_type': 'saturation',
        'marginal_effects': {'p25': 0.8, 'p50': 0.5, 'p75': 0.2}
    }
    effect_p25 = get_marginal_effect(nonlinear_edge, 100, 0.25)
    effect_p75 = get_marginal_effect(nonlinear_edge, 100, 0.75)
    assert effect_p25 == 0.8
    assert effect_p75 == 0.2
    print("  get_marginal_effect (nonlinear): PASS")

    # Test simple propagation
    adjacency = {
        'A': [{'target': 'B', 'beta': 0.5, 'std': 0.1}],
        'B': [{'target': 'C', 'beta': 0.3, 'std': 0.05}]
    }
    baseline = {'A': 100, 'B': 50, 'C': 25}
    intervention = {'A': 10}

    result = propagate_intervention_v31(
        adjacency, intervention, baseline,
        dampening_factor=1.0  # No dampening for test
    )
    assert result['converged']
    assert result['deltas']['A'] == 10
    # B should get effect from A
    assert result['deltas']['B'] > 0
    print("  propagate_intervention_v31: PASS")

    # Test edge resampling
    rng = np.random.default_rng(42)
    resampled = resample_edge_weights(adjacency, rng)
    # Beta should be different due to resampling
    original_beta = adjacency['A'][0]['beta']
    resampled_beta = resampled['A'][0]['beta']
    # With std=0.1 and multiplier=3.0, should be different
    print(f"  Edge resampling: {original_beta:.3f} -> {resampled_beta:.3f}")

    # Test compute_effects
    effects = compute_effects(baseline, result['values'])
    assert 'A' in effects
    assert 'percent_change' in effects['A']
    print("  compute_effects: PASS")

    # Test top effects
    top = get_top_effects(effects, top_n=2)
    assert len(top) <= 2
    print("  get_top_effects: PASS")

    print("-" * 40)
    print("All propagation tests PASSED\n")


if __name__ == "__main__":
    _run_tests()
