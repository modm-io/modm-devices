from pathlib import Path
import shutil
import urllib.parse
import urllib.request
import json
import re
from typing import Dict, List, Optional


SEARCH_API = "https://docs-be.nordicsemi.com/api/search"
OUTPUT_DIR = Path("../raw-device-data/nrf-devices")

# Kept aligned with the user-provided bundle query labels.
LABEL_KEYS = [
    "nrf53-series",
    "nrf5340",
    "thingy53",
    "nrf52-series",
    "nrf52840",
    "nrf52833",
    "nrf52832",
    "nrf52820",
    "nrf52811",
    "nrf52810",
    "nrf52805",
    "nrf51-series",
    "nrf51824",
    "nrf51822",
    "nrf51802",
    "nrf51422",
]


def _read_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "modm-devices raw nrf extractor",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))


def _download_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "modm-devices raw nrf extractor"},
    )
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8", errors="ignore")

def _iter_search_results_for_label(label: str) -> List[Dict]:
    query_params = [
        ("q", "product specification"),
        ("rpp", "100"),
        ("labelkey", label),
    ]
    next_url = SEARCH_API + "?" + urllib.parse.urlencode(query_params)

    results: List[Dict] = []
    while next_url:
        print(f"Querying search API [{label}]: {next_url}")
        payload = _read_json(next_url)
        results.extend(payload.get("Results", []))

        pagination = payload.get("Pagination") or {}
        next_url = pagination.get("next_page")

    return results


def _bundle_id_from_url(url: str) -> Optional[str]:
    match = re.search(r"/bundle/([^/]+)/", url)
    return match.group(1) if match else None


def _pin_page_candidates(bundle_id: str) -> List[str]:
    return [
        f"https://docs-be.nordicsemi.com/bundle/{bundle_id}/page/chapters/pin.html",
        f"https://docs-be.nordicsemi.com/bundle/{bundle_id}/page/pin.html",
    ]


def _safe_filename(bundle_id: str) -> str:
    return f"{bundle_id}-pin.html"


def _looks_like_pin_page(content: str) -> bool:
    lowered = content.lower()
    return "pin assignments" in lowered and "hardware and layout" in lowered


def _is_html_product_spec(leading: Dict) -> bool:
    url = (leading.get("url") or "").lower()
    title = (leading.get("publication_title") or leading.get("title") or "").lower()

    if "product specification" not in title:
        return False
    if "/page/" not in url:
        return False
    if "keyfeatures" not in url and "frontpage" not in url:
        return False
    return True


def main() -> None:
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    raw_results: List[Dict] = []
    for label in LABEL_KEYS:
        raw_results.extend(_iter_search_results_for_label(label))

    bundles: dict[str, dict] = {}
    for result in raw_results:
        leading = result.get("leading_result") or {}
        if not _is_html_product_spec(leading):
            continue

        bundle_id = leading.get("bundle_id")
        if not bundle_id:
            url = leading.get("url") or ""
            bundle_id = _bundle_id_from_url(url)
        if not bundle_id:
            continue

        bundles[bundle_id] = {
            "title": leading.get("publication_title") or leading.get("title") or bundle_id,
            "source_url": leading.get("url") or "",
        }

    if not bundles:
        raise RuntimeError("No nRF51/nRF52/nRF53 product-spec bundles discovered.")

    downloaded = []
    skipped = []

    for bundle_id in sorted(bundles):
        content = None
        page_url = None
        last_error = None

        for candidate in _pin_page_candidates(bundle_id):
            print(f"Downloading pin page: {bundle_id} -> {candidate}")
            try:
                candidate_content = _download_text(candidate)
            except Exception as error:
                last_error = str(error)
                continue

            if _looks_like_pin_page(candidate_content):
                content = candidate_content
                page_url = candidate
                break

        if content is None or page_url is None:
            reason = last_error or "missing pin assignments markers"
            print(f"  Skipping {bundle_id}: {reason}")
            skipped.append((bundle_id, reason))
            continue

        destination = OUTPUT_DIR / _safe_filename(bundle_id)
        destination.write_text(content, encoding="utf-8")
        downloaded.append((bundle_id, page_url, destination.name))

    manifest = {
        "source": SEARCH_API,
        "query": {
            "q": "product specification",
            "labelkey_per_request": LABEL_KEYS,
            "rpp": 100,
        },
        "downloaded": [
            {"bundle_id": bundle_id, "url": url, "file": filename}
            for bundle_id, url, filename in downloaded
        ],
        "skipped": [
            {"bundle_id": bundle_id, "reason": reason}
            for bundle_id, reason in skipped
        ],
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"Downloaded {len(downloaded)} pin pages into {OUTPUT_DIR}")
    if skipped:
        print(f"Skipped {len(skipped)} bundles (see manifest.json)")


if __name__ == "__main__":
    main()
