"""Driver: python src/run_engine.py <case> [baseline|ptdf|overload|verify|classify|notes|all]

case in WP2024s42, WP2033s42, WP2033s43. Default stage = all:
classification -> prepare -> baseline solve -> PTDF/LODF/shift factors -> overload series.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine_prep as ep  # noqa: E402

if __name__ == "__main__":
    case = sys.argv[1]
    stage = sys.argv[2] if len(sys.argv) > 2 else "all"
    assert case in ep.CASES, case
    t0 = time.time()
    if stage in ("all", "baseline"):
        san = ep.run_baseline(case)
    if stage in ("all", "ptdf"):
        res = ep.compute_ptdf_lodf(case)
    if stage in ("all", "overload"):
        st = ep.overload_series(case)
    if stage in ("all", "verify"):
        ep.verify_lodf_dcpf(case)
    if stage == "classify":
        ep.classify_group(case)
    if stage == "notes":
        import engine_notes
        engine_notes.main(sys.argv[3:] or list(ep.CASES))
    ep.log(f"[{case}] stage {stage} done in {time.time() - t0:.0f}s")
