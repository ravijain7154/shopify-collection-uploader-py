import csv
import json
import sys
from typing import Dict, Tuple

import requests


API_VERSION = "2021-04"
CSV_PATH = "VariableFromFile.csv"
COLUMN_NAME = "VariableFromFile"


def normalize_shop_domain(shop_input: str) -> str:
    shop = shop_input.strip()
    if shop.startswith("http://") or shop.startswith("https://"):
        shop = shop.split("://", 1)[1]
    shop = shop.rstrip("/")
    return shop


def build_url(shop_domain: str) -> str:
    return f"https://{shop_domain}/admin/api/{API_VERSION}/smart_collections.json"


def parse_row_payload(raw_value: str, row_num: int) -> Tuple[Dict, str]:
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return {}, f"Row {row_num}: empty payload in column '{COLUMN_NAME}'."
    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        return {}, f"Row {row_num}: invalid JSON in column '{COLUMN_NAME}': {exc}"
    if not isinstance(payload, dict) or "smart_collection" not in payload:
        return {}, f"Row {row_num}: payload must be an object with key 'smart_collection'."
    return payload, ""


def upload_payload(url: str, api_key: str, payload: Dict) -> Tuple[bool, str]:
    headers = {
        "X-Shopify-Access-Token": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        return False, f"Request failed: {exc}"
    if 200 <= resp.status_code < 300:
        return True, f"Created (HTTP {resp.status_code})"
    return False, f"HTTP {resp.status_code}: {resp.text[:500]}"


def main() -> int:
    print("Shopify Smart Collection Uploader")
    shop_input = input("Enter Shopify store URL or domain (e.g., myshop.myshopify.com): ").strip()
    api_key = input("Enter Shopify API Key (X-Shopify-Access-Token): ").strip()

    if not shop_input or not api_key:
        print("Error: store and API key are required.")
        return 1

    shop_domain = normalize_shop_domain(shop_input)
    url = build_url(shop_domain)

    try:
        with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if COLUMN_NAME not in reader.fieldnames:
                print(f"Error: column '{COLUMN_NAME}' not found in {CSV_PATH}.")
                print(f"Available columns: {reader.fieldnames}")
                return 1

            success_count = 0
            fail_count = 0
            for idx, row in enumerate(reader, start=2):  # header is row 1
                payload, err = parse_row_payload(row.get(COLUMN_NAME, ""), idx)
                if err:
                    print(f"[SKIP] {err}")
                    fail_count += 1
                    continue

                ok, msg = upload_payload(url, api_key, payload)
                if ok:
                    success_count += 1
                    title = payload.get("smart_collection", {}).get("title", "Untitled")
                    print(f"[OK] Row {idx}: {title} -> {msg}")
                else:
                    fail_count += 1
                    print(f"[FAIL] Row {idx}: {msg}")

            print(f"\nDone. Success: {success_count}, Failed: {fail_count}")
    except FileNotFoundError:
        print(f"Error: {CSV_PATH} not found.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
