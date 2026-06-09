#!/usr/bin/env python3
"""
Fetch real nearest competitor store locations for each Copart facility.
Uses Nominatim (geocoding) and Overpass API (store lookup) — both free, no API key.
Results cached in data/store_locations.json.

Usage: python3 scripts/fetch_store_locations.py
Runtime: ~10-15 minutes (rate-limited to respect free APIs)
"""

import json
import math
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = BASE_DIR / "data" / "store_locations.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "CopartCompAnalysis/1.0 (compensation research)"

COMPETITORS = {
    "walmart": {"wikidata": "Q483551", "label": "Walmart"},
    "home_depot": {"wikidata": "Q864407", "label": "Home Depot"},
    "costco": {"wikidata": "Q715583", "label": "Costco"},
    "starbucks": {"wikidata": "Q37158", "label": "Starbucks"},
}

SEARCH_RADIUS_M = 80000  # 50 miles in meters


def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def http_get(url, params=None, retries=3):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    Retry in {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"    Failed after {retries} attempts: {e}")
                return None


def http_post(url, data, retries=3):
    req = urllib.request.Request(
        url,
        data=data.encode(),
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    Retry in {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"    Failed after {retries} attempts: {e}")
                return None


def geocode(address):
    result = http_get(NOMINATIM_URL, {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    })
    if result and len(result) > 0:
        return float(result[0]["lat"]), float(result[0]["lon"])
    return None, None


def find_nearest_store(lat, lon, wikidata_id):
    query = f"""
[out:json][timeout:30];
(
  nwr["brand:wikidata"="{wikidata_id}"](around:{SEARCH_RADIUS_M},{lat},{lon});
);
out center;
"""
    data = "data=" + urllib.parse.quote(query)
    result = http_post(OVERPASS_URL, data)
    if not result or "elements" not in result:
        return None

    best = None
    best_dist = float("inf")
    for el in result["elements"]:
        slat = el.get("lat") or (el.get("center", {}).get("lat"))
        slon = el.get("lon") or (el.get("center", {}).get("lon"))
        if slat is None or slon is None:
            continue
        dist = haversine(lat, lon, slat, slon)
        if dist < best_dist:
            best_dist = dist
            tags = el.get("tags", {})
            addr_parts = []
            if tags.get("addr:housenumber") and tags.get("addr:street"):
                addr_parts.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
            elif tags.get("addr:street"):
                addr_parts.append(tags["addr:street"])
            city = tags.get("addr:city", "")
            state = tags.get("addr:state", "")
            postcode = tags.get("addr:postcode", "")
            if city:
                addr_parts.append(city)
            if state:
                addr_parts.append(state)
            if postcode:
                addr_parts.append(postcode)
            address = ", ".join(addr_parts) if addr_parts else f"{slat:.5f}, {slon:.5f}"
            best = {
                "name": tags.get("name", tags.get("brand", "")),
                "address": address,
                "lat": round(slat, 6),
                "lon": round(slon, 6),
                "distance_mi": round(best_dist, 1),
            }
    return best


def load_copart_locations():
    from generate_data import COPART_LOCATIONS
    return COPART_LOCATIONS


def main():
    # Load existing cache
    cache = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())
        print(f"Loaded cache: {len(cache)} locations")

    # Load Copart locations
    import sys
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from generate_data import COPART_LOCATIONS

    total = len(COPART_LOCATIONS)
    print(f"\nProcessing {total} Copart locations...")

    for i, (name, city, state, address, zipcode) in enumerate(COPART_LOCATIONS):
        if zipcode in cache and cache[zipcode].get("copart_lat"):
            existing = cache[zipcode]
            has_all = all(
                existing.get(comp) is not None or existing.get(f"{comp}_searched")
                for comp in COMPETITORS
            )
            if has_all:
                print(f"  [{i+1}/{total}] {name} — cached")
                continue

        print(f"  [{i+1}/{total}] {name} ({city}, {state})")

        # Geocode Copart address
        full_addr = f"{address}, {city}, {state} {zipcode}"
        entry = cache.get(zipcode, {})

        if not entry.get("copart_lat"):
            lat, lon = geocode(full_addr)
            time.sleep(1.1)  # Nominatim rate limit
            if lat is None:
                print(f"    !! Could not geocode: {full_addr}")
                continue
            entry["copart_lat"] = lat
            entry["copart_lon"] = lon
            print(f"    Geocoded: {lat:.4f}, {lon:.4f}")
        else:
            lat = entry["copart_lat"]
            lon = entry["copart_lon"]

        # Find nearest competitor stores
        for comp_key, comp_info in COMPETITORS.items():
            if entry.get(comp_key) is not None or entry.get(f"{comp_key}_searched"):
                continue
            store = find_nearest_store(lat, lon, comp_info["wikidata"])
            time.sleep(1.5)  # Be polite to Overpass
            if store:
                entry[comp_key] = store
                print(f"    {comp_info['label']}: {store['name']} — {store['distance_mi']} mi")
            else:
                entry[comp_key] = None
                entry[f"{comp_key}_searched"] = True
                print(f"    {comp_info['label']}: not found within {SEARCH_RADIUS_M/1609:.0f} mi")

        cache[zipcode] = entry

        # Save after each location
        os.makedirs(CACHE_PATH.parent, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=2))

    # Summary
    found = {comp: 0 for comp in COMPETITORS}
    for z, data in cache.items():
        for comp in COMPETITORS:
            if data.get(comp):
                found[comp] += 1
    print(f"\nDone! {len(cache)} locations cached.")
    for comp, label_info in COMPETITORS.items():
        print(f"  {label_info['label']}: {found[comp]}/{len(cache)} found")
    print(f"Saved to {CACHE_PATH}")


if __name__ == "__main__":
    main()
