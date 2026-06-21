#!/usr/bin/env python3
"""
Simple HTTP load testing script (no third-party dependencies).

Examples:
  python3 scripts/load_test.py --url http://localhost:8080/health --requests 1000 --concurrency 20
  python3 scripts/load_test.py --url http://localhost:8080/api/ping --duration 30 --concurrency 50
  python3 scripts/load_test.py --url https://example.com/api --method POST \
    --header "Content-Type: application/json" --body '{"hello":"world"}'
"""

from __future__ import annotations

import argparse
import json
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from typing import Optional


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.latencies_ms: list[float] = []
        self.success = 0
        self.fail = 0
        self.status_codes: Counter[int] = Counter()
        self.errors: Counter[str] = Counter()

    def record(self, latency_ms: float, status_code: Optional[int], err: Optional[str]) -> None:
        with self._lock:
            self.latencies_ms.append(latency_ms)
            if status_code is not None:
                self.status_codes[status_code] += 1
                if 200 <= status_code <= 399:
                    self.success += 1
                else:
                    self.fail += 1
            else:
                self.fail += 1
            if err:
                self.errors[err] += 1


def parse_headers(raw_headers: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for item in raw_headers:
        if ":" not in item:
            raise ValueError(f"Invalid header format: {item!r}. Expected 'Key: Value'.")
        key, value = item.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = int(round((p / 100.0) * (len(sorted_values) - 1)))
    return sorted_values[idx]


def make_request(
    url: str,
    method: str,
    headers: dict[str, str],
    body: Optional[bytes],
    timeout: float,
    ssl_context: Optional[ssl.SSLContext],
) -> tuple[float, Optional[int], Optional[str]]:
    req = urllib.request.Request(url=url, method=method, headers=headers, data=body)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
            _ = resp.read()
            latency_ms = (time.perf_counter() - start) * 1000.0
            return latency_ms, resp.status, None
    except urllib.error.HTTPError as http_err:
        _ = http_err.read()
        latency_ms = (time.perf_counter() - start) * 1000.0
        return latency_ms, http_err.code, f"HTTPError:{http_err.code}"
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.perf_counter() - start) * 1000.0
        return latency_ms, None, type(exc).__name__


def run_requests_mode(
    total_requests: int,
    concurrency: int,
    worker_fn,
) -> None:
    counter = {"value": 0}
    lock = threading.Lock()

    def worker() -> None:
        while True:
            with lock:
                if counter["value"] >= total_requests:
                    return
                counter["value"] += 1
            worker_fn()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def run_duration_mode(
    duration_seconds: float,
    concurrency: int,
    worker_fn,
) -> None:
    stop_at = time.perf_counter() + duration_seconds

    def worker() -> None:
        while time.perf_counter() < stop_at:
            worker_fn()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def print_report(metrics: Metrics, elapsed_seconds: float, show_errors: int) -> None:
    latencies = sorted(metrics.latencies_ms)
    total = len(latencies)
    success_rate = (metrics.success / total * 100.0) if total else 0.0
    rps = (total / elapsed_seconds) if elapsed_seconds > 0 else 0.0

    report = {
        "total_requests": total,
        "success": metrics.success,
        "fail": metrics.fail,
        "success_rate_percent": round(success_rate, 2),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "requests_per_second": round(rps, 2),
        "latency_ms": {
            "min": round(latencies[0], 2) if latencies else 0.0,
            "avg": round(sum(latencies) / total, 2) if total else 0.0,
            "p50": round(percentile(latencies, 50), 2) if latencies else 0.0,
            "p90": round(percentile(latencies, 90), 2) if latencies else 0.0,
            "p95": round(percentile(latencies, 95), 2) if latencies else 0.0,
            "p99": round(percentile(latencies, 99), 2) if latencies else 0.0,
            "max": round(latencies[-1], 2) if latencies else 0.0,
        },
        "status_codes": dict(sorted(metrics.status_codes.items(), key=lambda x: x[0])),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if metrics.errors and show_errors > 0:
        print("\nTop errors:")
        for err, cnt in metrics.errors.most_common(show_errors):
            print(f"  - {err}: {cnt}")


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HTTP load testing script")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--method", default="GET", help="HTTP method (default: GET)")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent workers")
    parser.add_argument(
        "--requests",
        type=int,
        default=0,
        help="Total requests to send (use with --duration=0)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0,
        help="Run duration in seconds (if > 0, overrides --requests)",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Per request timeout seconds")
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Request header: 'Key: Value' (can be provided multiple times)",
    )
    parser.add_argument("--body", default="", help="Request body")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS certificate validation")
    parser.add_argument(
        "--show-errors",
        type=int,
        default=5,
        help="How many top errors to print (default: 5)",
    )
    args = parser.parse_args()

    if args.concurrency <= 0:
        parser.error("--concurrency must be > 0")
    if args.duration <= 0 and args.requests <= 0:
        parser.error("Either --duration > 0 or --requests > 0 is required")
    return args


def main() -> None:
    args = build_args()
    method = args.method.upper()
    headers = parse_headers(args.header)
    body: Optional[bytes] = args.body.encode("utf-8") if args.body else None
    ssl_context = None
    if args.insecure:
        ssl_context = ssl._create_unverified_context()

    metrics = Metrics()
    start = time.perf_counter()

    def worker_fn() -> None:
        latency_ms, status_code, err = make_request(
            url=args.url,
            method=method,
            headers=headers,
            body=body,
            timeout=args.timeout,
            ssl_context=ssl_context,
        )
        metrics.record(latency_ms, status_code, err)

    if args.duration > 0:
        run_duration_mode(duration_seconds=args.duration, concurrency=args.concurrency, worker_fn=worker_fn)
    else:
        run_requests_mode(total_requests=args.requests, concurrency=args.concurrency, worker_fn=worker_fn)

    elapsed = time.perf_counter() - start
    print_report(metrics, elapsed_seconds=elapsed, show_errors=args.show_errors)


if __name__ == "__main__":
    main()
