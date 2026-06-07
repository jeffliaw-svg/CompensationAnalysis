#!/usr/bin/env python3
"""
Verify build integrity for the Copart Compensation Analysis dashboard.
Checks data.json, index.html, gh-pages staleness, and removed artifacts.
Exit code 0 = all pass, 1 = any fail.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXPECTED_LOCATIONS = 197

STATE_MIN_WAGE = {
    "AL": 7.25, "AK": 11.91, "AZ": 14.70, "AR": 11.00,
    "CA": 16.50, "CO": 14.81, "CT": 15.69, "DE": 13.25,
    "FL": 13.00, "GA": 7.25, "HI": 14.00, "ID": 7.25,
    "IL": 14.00, "IN": 7.25, "IA": 7.25, "KS": 7.25,
    "KY": 7.25, "LA": 7.25, "ME": 14.15, "MD": 15.00,
    "MA": 15.00, "MI": 10.56, "MN": 11.13, "MS": 7.25,
    "MO": 13.75, "MT": 10.55, "NE": 13.50, "NV": 12.00,
    "NH": 7.25, "NJ": 15.49, "NM": 12.00, "NY": 15.50,
    "NC": 7.25, "ND": 7.25, "OH": 10.70, "OK": 7.25,
    "OR": 14.70, "PA": 7.25, "RI": 15.00, "SC": 7.25,
    "SD": 11.45, "TN": 7.25, "TX": 7.25, "UT": 7.25,
    "VT": 14.01, "VA": 12.41, "WA": 16.66, "WV": 8.75,
    "WI": 7.25, "WY": 7.25,
}


def check_data_integrity():
    results = []
    path = BASE_DIR / "public" / "data.json"
    if not path.exists():
        return [("FAIL", "public/data.json does not exist")]

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [("FAIL", f"public/data.json is invalid JSON: {e}")]

    locs = data.get("locations", [])
    n = len(locs)
    results.append(("PASS" if n == EXPECTED_LOCATIONS else "FAIL",
                     f"Location count: {n} (expected {EXPECTED_LOCATIONS})"))

    required = ["blended_wage_outdoor", "blended_wage_indoor", "quartile",
                 "in_range", "nearest_distance_mi", "employers", "address"]
    missing = {}
    has_old_blended = []
    for loc in locs:
        for field in required:
            if field not in loc:
                missing.setdefault(field, []).append(loc.get("yard", "?"))
        if "blended_wage" in loc:
            has_old_blended.append(loc.get("yard", "?"))

    if missing:
        for field, yards in missing.items():
            results.append(("FAIL", f"Missing '{field}' in {len(yards)} locations (e.g. {yards[0]})"))
    else:
        results.append(("PASS", "All locations have required fields"))

    if has_old_blended:
        results.append(("FAIL", f"Old 'blended_wage' field found in {len(has_old_blended)} locations"))
    else:
        results.append(("PASS", "No stale 'blended_wage' field"))

    # Quartile distribution
    from collections import Counter
    q_dist = Counter(loc.get("quartile") for loc in locs)
    balanced = all(49 <= q_dist.get(q, 0) <= 50 for q in [1, 2, 3, 4])
    results.append(("PASS" if balanced else "FAIL",
                     f"Quartile distribution: {dict(sorted(q_dist.items()))}"))

    # Minimum wage compliance
    violations = []
    for loc in locs:
        st = loc.get("state", "")
        min_w = STATE_MIN_WAGE.get(st, 7.25)
        for key, emp in (loc.get("employers") or {}).items():
            if isinstance(emp, dict) and emp.get("hourly_low", 999) < min_w - 0.01:
                violations.append(f"{loc['yard']} {key}: ${emp['hourly_low']} < ${min_w}")
    if violations:
        results.append(("FAIL", f"Min wage violations: {len(violations)} (e.g. {violations[0]})"))
    else:
        results.append(("PASS", "All wages >= state minimum"))

    # Source URLs
    missing_urls = 0
    for loc in locs:
        for key, emp in (loc.get("employers") or {}).items():
            if isinstance(emp, dict) and not emp.get("source_url"):
                missing_urls += 1
    results.append(("PASS" if missing_urls == 0 else "FAIL",
                     f"Source URLs: {missing_urls} missing"))

    # No "Copart " prefix
    prefixed = [loc["yard"] for loc in locs if loc.get("yard", "").startswith("Copart ")]
    if prefixed:
        results.append(("FAIL", f"'Copart ' prefix in {len(prefixed)} yards (e.g. {prefixed[0]})"))
    else:
        results.append(("PASS", "No 'Copart ' prefix in yard names"))

    return results


def check_html_integrity():
    results = []
    path = BASE_DIR / "public" / "index.html"
    if not path.exists():
        return [("FAIL", "public/index.html does not exist")]

    html = path.read_text()
    size = path.stat().st_size

    results.append(("PASS" if size < 2_097_152 else "FAIL",
                     f"HTML size: {size:,} bytes (<2MB)"))
    results.append(("PASS" if size > 100_000 else "FAIL",
                     f"HTML size sanity: {size:,} bytes (>100KB)"))

    has_chartjs = bool(re.search(r'chart\.js', html, re.IGNORECASE))
    results.append(("FAIL" if has_chartjs else "PASS", "No Chart.js CDN reference"))

    has_canvas = "<canvas" in html
    results.append(("FAIL" if has_canvas else "PASS", "No <canvas> elements"))

    has_bls = bool(re.search(r'\bBLS\b', html))
    results.append(("FAIL" if has_bls else "PASS", "No BLS references"))

    has_toggle = 'id="roleToggle"' in html or "id='roleToggle'" in html
    results.append(("PASS" if has_toggle else "FAIL", "Indoor/outdoor toggle present"))

    has_outdoor = "blended_wage_outdoor" in html
    has_indoor = "blended_wage_indoor" in html
    results.append(("PASS" if has_outdoor and has_indoor else "FAIL",
                     "Both blended_wage_outdoor and _indoor in data"))

    bare_blended_dot = bool(re.search(r'\.blended_wage\b(?!_)', html))
    bare_blended_json = bool(re.search(r'"blended_wage"\s*:', html))
    if bare_blended_dot or bare_blended_json:
        results.append(("FAIL", "Stale bare 'blended_wage' reference found"))
    else:
        results.append(("PASS", "No stale bare 'blended_wage' references"))

    has_assign = "function assignQuartiles" in html
    results.append(("PASS" if has_assign else "FAIL", "assignQuartiles function present"))

    return results


def _git(*args):
    r = subprocess.run(["git", "-C", str(BASE_DIR)] + list(args),
                       capture_output=True, text=True)
    return r


def check_staleness():
    results = []
    local_path = BASE_DIR / "public" / "index.html"
    if not local_path.exists():
        return [("FAIL", "public/index.html missing, can't compare")]

    local_hash = hashlib.sha256(local_path.read_bytes()).hexdigest()[:16]

    r = _git("show", "gh-pages:index.html")
    if r.returncode != 0:
        results.append(("FAIL", "gh-pages branch or root index.html not found"))
        return results

    ghp_hash = hashlib.sha256(r.stdout.encode()).hexdigest()[:16]
    if local_hash == ghp_hash:
        results.append(("PASS", f"gh-pages root index.html matches local ({local_hash})"))
    else:
        results.append(("FAIL", f"gh-pages STALE: local={local_hash} vs gh-pages={ghp_hash}"))

    return results


def check_removed_artifacts():
    results = []

    bls_dir = BASE_DIR / "data" / "bls"
    if bls_dir.exists():
        results.append(("FAIL", "data/bls/ directory still exists"))
    else:
        results.append(("PASS", "No data/bls/ directory"))

    r = _git("ls-tree", "-r", "--name-only", "gh-pages")
    if r.returncode == 0:
        bls_on_ghp = [f for f in r.stdout.splitlines() if f.startswith("data/bls/")]
        if bls_on_ghp:
            results.append(("FAIL", f"BLS files on gh-pages: {bls_on_ghp}"))
        else:
            results.append(("PASS", "No BLS artifacts on gh-pages"))

    return results


def main():
    print("=" * 60)
    print("Copart Compensation Analysis - Build Verification")
    print("=" * 60)

    all_results = []
    for name, func in [
        ("Data Integrity", check_data_integrity),
        ("HTML Integrity", check_html_integrity),
        ("Staleness", check_staleness),
        ("Removed Artifacts", check_removed_artifacts),
    ]:
        print(f"\n--- {name} ---")
        results = func()
        all_results.extend(results)
        for status, msg in results:
            print(f"  [{status}] {msg}")

    failures = [r for r in all_results if r[0] == "FAIL"]
    passes = [r for r in all_results if r[0] == "PASS"]
    print(f"\n{'=' * 60}")
    print(f"Results: {len(passes)} passed, {len(failures)} failed")
    if failures:
        print("\nFailures:")
        for _, msg in failures:
            print(f"  - {msg}")
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
