"""
Basic load test against a running instance of this app. Deliberately
dependency-free (uses only requests and the standard library concurrent.
futures) so it can be run without installing anything extra.

This is not a substitute for a real load testing setup (Locust, k6) before
a genuine production launch, it is a first, honest measurement: does the
app fall over or slow to a crawl under concurrent load, using its own real
endpoints, not synthetic numbers.

Usage
-----
    python scripts/load_test.py --base-url http://127.0.0.1:8001 --username admin --password admin1234
    python scripts/load_test.py --base-url http://127.0.0.1:8001 --username admin --password admin1234 --concurrency 20 --requests 200
"""
import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def login(base_url: str, username: str, password: str) -> str:
    resp = requests.post(f"{base_url}/api/v1/auth/login/", json={"username": username, "password": password}, timeout=10)
    resp.raise_for_status()
    return resp.json()["access"]


def timed_request(base_url: str, path: str, token: str) -> float:
    start = time.monotonic()
    try:
        resp = requests.get(f"{base_url}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        ok = resp.status_code < 500
    except requests.RequestException:
        ok = False
    elapsed = time.monotonic() - start
    return elapsed, ok


def run_load_test(base_url: str, token: str, path: str, concurrency: int, total_requests: int):
    print(f"Load testing {path} : {total_requests} requests, concurrency {concurrency}")
    latencies = []
    failures = 0

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(timed_request, base_url, path, token) for _ in range(total_requests)]
        for future in as_completed(futures):
            elapsed, ok = future.result()
            latencies.append(elapsed)
            if not ok:
                failures += 1

    latencies.sort()

    def percentile(p):
        idx = min(int(len(latencies) * p), len(latencies) - 1)
        return latencies[idx]

    print(f"  requests: {total_requests}  failures: {failures}")
    print(f"  min: {min(latencies):.3f}s  mean: {statistics.mean(latencies):.3f}s  max: {max(latencies):.3f}s")
    print(f"  p50: {percentile(0.50):.3f}s  p95: {percentile(0.95):.3f}s  p99: {percentile(0.99):.3f}s")
    print()


def main():
    parser = argparse.ArgumentParser(description="Basic concurrent load test against a running instance")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--requests", type=int, default=100)
    args = parser.parse_args()

    print(f"Logging in as {args.username}...")
    token = login(args.base_url, args.username, args.password)
    print("Logged in.\n")

    paths_to_test = [
        "/api/v1/jobs/?page_size=50",
        "/api/v1/candidates/?page_size=50",
        "/healthz/",
    ]
    for path in paths_to_test:
        run_load_test(args.base_url, token, path, args.concurrency, args.requests)


if __name__ == "__main__":
    main()
