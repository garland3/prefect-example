"""Latin Hypercube DOE runner — samples parameter space and evaluates each point."""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats.qmc import LatinHypercube

# Parameter bounds: (min, max)
BOUNDS = {
    "temperature": (100.0, 500.0),
    "pressure": (1.0, 50.0),
    "catalyst_ratio": (0.01, 1.0),
}


def load_flow():
    """Dynamically import evaluation_pipeline from generated_flow.py."""
    flow_path = Path(__file__).parent / "generated_flow.py"
    if not flow_path.exists():
        raise FileNotFoundError(
            f"{flow_path} not found. Run flow_designer.py first."
        )
    spec = importlib.util.spec_from_file_location("generated_flow", flow_path)
    mod = importlib.util.module_from_spec(spec)
    # Ensure generated_tasks is importable from same directory
    sys.path.insert(0, str(flow_path.parent))
    spec.loader.exec_module(mod)
    return mod.evaluation_pipeline


def run_doe(n_samples: int = 10, seed: int = 42) -> list[dict]:
    pipeline = load_flow()
    sampler = LatinHypercube(d=len(BOUNDS), seed=seed)
    raw = sampler.random(n=n_samples)

    param_names = list(BOUNDS.keys())
    results = []

    for i, sample in enumerate(raw):
        params = {}
        for j, name in enumerate(param_names):
            lo, hi = BOUNDS[name]
            params[name] = round(lo + sample[j] * (hi - lo), 4)

        print(f"[{i+1}/{n_samples}] {params}")
        try:
            result = pipeline(**params)
            if isinstance(result, str):
                result = json.loads(result)
            results.append(result)
            print(f"  -> yield: {result.get('yield_pct', '?')}%")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            results.append({"error": str(e), "parameters": params})

    # Summary
    yields = [r["yield_pct"] for r in results if "yield_pct" in r]
    if yields:
        best_idx = np.argmax(yields)
        print(f"\n{'='*50}")
        print(f"DOE Summary: {len(yields)}/{n_samples} successful")
        print(f"  Mean yield: {np.mean(yields):.2f}%")
        print(f"  Best yield: {max(yields):.2f}%")
        print(f"  Best params: {results[best_idx].get('parameters', '?')}")

    return results


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_doe(n_samples=n)
