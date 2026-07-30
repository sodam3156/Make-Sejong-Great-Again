#!/usr/bin/env python3
"""Capture a Day 3 browser-to-API integration run as auditable evidence.

The browser is allowed to reach only localhost/127.0.0.1.  A normal run follows
the UI's real three-minute autoplay.  ``--fast`` is useful only as a wiring
check and is deliberately marked non-gate evidence in the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    from playwright.sync_api import BrowserContext, Page, Route, sync_playwright
except ImportError as error:  # pragma: no cover - exercised on operator machines
    raise SystemExit(
        "Playwright is required for evidence capture. "
        "Install it in the evidence environment with: python -m pip install playwright"
    ) from error


CAPTURE_STATES = {
    "normal",
    "rain_warning",
    "spillback",
    "policy_compare",
    "safety_review",
    "operator_approval",
    "recovery_compare",
}
REQUIRED_AUDIT_EVENTS = {"simulation_created", "approval_decided"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(repo: Path, *args: str) -> str:
    command = ["git", "-C", str(repo), *args]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        if os.name != "nt":
            return "unavailable"
        try:
            converted = subprocess.run(
                ["wsl.exe", "wslpath", "-a", "-u", str(repo)],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).stdout.strip()
            completed = subprocess.run(
                ["wsl.exe", "git", "-C", converted, *args],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.CalledProcessError):
            return "unavailable"
    return completed.stdout.strip()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def get_json(base_url: str, relative_url: str) -> tuple[int, Any]:
    url = urljoin(base_url.rstrip("/") + "/", relative_url.lstrip("/"))
    parsed = urlparse(url)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError(f"refusing non-local evidence request: {url}")
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "RainFlow-Day3-Evidence/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {url} returned {error.code}: {body}") from error


def browser_state(page: Page) -> dict[str, Any]:
    label = page.locator("#state-label").inner_text()
    position, _, display_label = label.partition("—")
    current, total = (int(part.strip()) for part in position.strip().split("/", 1))
    active_dot = page.locator(".step-dot.active")
    state = active_dot.get_attribute("title") if active_dot.count() else None
    return {
        "current": current,
        "total": total,
        "screen_state": state,
        "display_label": display_label.strip(),
        "clock": page.locator("#clock").inner_text(),
    }


def install_local_only_route(
    context: BrowserContext,
    request_log: list[dict[str, Any]],
) -> None:
    def handle(route: Route) -> None:
        request = route.request
        parsed = urlparse(request.url)
        allowed = parsed.scheme in {"data", "about", "blob"} or (
            parsed.scheme in {"http", "https"}
            and parsed.hostname in {"127.0.0.1", "localhost"}
        )
        request_log.append(
            {
                "at_utc": utc_now(),
                "method": request.method,
                "resource_type": request.resource_type,
                "url": request.url,
                "decision": "allowed" if allowed else "blocked",
            }
        )
        if allowed:
            route.continue_()
        else:
            route.abort("blockedbyclient")

    context.route("**/*", handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765/")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release-zip", type=Path)
    parser.add_argument("--browser-channel", default="msedge")
    parser.add_argument(
        "--expected-duration-seconds",
        type=float,
        default=180.0,
        help="minimum elapsed time for a gate run",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="click through states quickly; output is a wiring check, not gate evidence",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir()
    har_path = output_dir / "localhost.har"

    repo = args.repo.resolve()
    base_url = args.base_url.rstrip("/") + "/"
    parsed_base = urlparse(base_url)
    if parsed_base.scheme != "http" or parsed_base.hostname not in {
        "127.0.0.1",
        "localhost",
    }:
        raise SystemExit("--base-url must be an http:// localhost or 127.0.0.1 URL")

    started_wall = time.monotonic()
    transitions: list[dict[str, Any]] = []
    browser_requests: list[dict[str, Any]] = []
    browser_responses: list[dict[str, Any]] = []
    console_events: list[dict[str, Any]] = []
    page_errors: list[dict[str, Any]] = []
    captured_states: set[str] = set()
    run_id = ""
    failure: str | None = None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel=args.browser_channel,
            headless=True,
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1100},
            locale="ko-KR",
            record_har_path=str(har_path),
            record_har_mode="full",
            record_har_content="embed",
        )
        install_local_only_route(context, browser_requests)
        page = context.new_page()
        page.on(
            "response",
            lambda response: browser_responses.append(
                {
                    "at_utc": utc_now(),
                    "status": response.status,
                    "url": response.url,
                }
            ),
        )
        page.on(
            "console",
            lambda message: console_events.append(
                {
                    "at_utc": utc_now(),
                    "type": message.type,
                    "text": message.text,
                }
            ),
        )
        page.on(
            "pageerror",
            lambda error: page_errors.append(
                {"at_utc": utc_now(), "error": str(error)}
            ),
        )

        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=30_000)
            page.locator("#badge-source").wait_for(state="visible", timeout=10_000)
            page.wait_for_function(
                """() => {
                  const badge = document.querySelector('#badge-source');
                  const run = document.querySelector('#run-id');
                  return badge && badge.textContent.trim() ===
                    'result_source: live_simulation' &&
                    run && run.textContent.trim().startsWith('live-');
                }""",
                timeout=15_000,
            )
            run_id = page.locator("#run-id").inner_text().strip()
            if args.fast and page.locator("#btn-playpause").inner_text() == "일시정지":
                page.locator("#btn-playpause").click()

            previous_key: tuple[int, str | None] | None = None
            approval_clicked = False
            while True:
                state = browser_state(page)
                key = (state["current"], state["screen_state"])
                if key != previous_key:
                    transition = {
                        **state,
                        "elapsed_seconds": round(time.monotonic() - started_wall, 3),
                        "at_utc": utc_now(),
                    }
                    transitions.append(transition)
                    previous_key = key

                screen_state = state["screen_state"]
                if screen_state in CAPTURE_STATES and screen_state not in captured_states:
                    screenshot_path = screenshots_dir / (
                        f"{state['current']:02d}-{screen_state}.png"
                    )
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    captured_states.add(screen_state)

                if screen_state == "operator_approval" and not approval_clicked:
                    page.locator("#btn-approve").click()
                    approval_clicked = True
                    page.wait_for_function(
                        """() => {
                          const note = document.querySelector('#decision-note');
                          return note && note.textContent.includes('(live)');
                        }""",
                        timeout=15_000,
                    )
                    page.screenshot(
                        path=str(screenshots_dir / "operator-approval-approved.png"),
                        full_page=True,
                    )

                if state["current"] == state["total"]:
                    break

                if args.fast:
                    page.locator("#btn-next").click()
                    page.wait_for_timeout(150)
                else:
                    page.wait_for_timeout(250)

            elapsed = time.monotonic() - started_wall
            if not args.fast and elapsed < args.expected_duration_seconds:
                page.wait_for_timeout(
                    int((args.expected_duration_seconds - elapsed) * 1000)
                )
            page.screenshot(
                path=str(screenshots_dir / "final-20-of-20.png"),
                full_page=True,
            )
        except Exception as error:
            failure = f"{type(error).__name__}: {error}"
            try:
                page.screenshot(
                    path=str(screenshots_dir / "failure.png"),
                    full_page=True,
                )
            except Exception:
                pass
        finally:
            context.close()
            browser.close()

    status_health, health = get_json(base_url, "/api/health")
    run: dict[str, Any] = {}
    audit: dict[str, Any] = {}
    status_run = 0
    status_audit = 0
    if run_id:
        status_run, run = get_json(base_url, f"/api/simulations/{run_id}")
        status_audit, audit = get_json(base_url, f"/api/audit/{run_id}")
    write_json(output_dir / "health.json", health)
    write_json(output_dir / "run.json", run)
    write_json(output_dir / "audit.json", audit)
    write_json(output_dir / "browser-requests.json", browser_requests)
    write_json(output_dir / "browser-responses.json", browser_responses)
    write_json(output_dir / "console-events.json", console_events)
    write_json(output_dir / "page-errors.json", page_errors)
    write_json(output_dir / "timeline-transitions.json", transitions)

    elapsed_seconds = round(time.monotonic() - started_wall, 3)
    event_names = {
        event.get("event")
        for event in audit.get("events", [])
        if isinstance(event, dict)
    }
    policies = {
        item.get("policy_id"): item
        for item in run.get("policies", [])
        if isinstance(item, dict)
    }
    applied_policy_id = (
        run.get("recovery_compare", {}).get("applied_policy_id")
        if isinstance(run, dict)
        else None
    )
    applied = run.get("recovery_compare", {}).get("applied", {})
    baseline = policies.get("no_action", {}).get("kpi", {})
    all_local = all(
        item["decision"] == "blocked"
        or urlparse(item["url"]).hostname in {"127.0.0.1", "localhost", None}
        for item in browser_requests
    )
    assertions = {
        "browser_allowed_only_local_requests": all_local,
        "health_http_200": status_health == 200,
        "llm_rule_based_fallback": health.get("llm") == "rule_based_fallback",
        "simulation_http_200": status_run == 200,
        "audit_http_200": status_audit == 200,
        "run_id_is_live": run_id.startswith("live-"),
        "result_source_live_simulation": run.get("result_source")
        == "live_simulation",
        "simulator_version_rainflow_queue_v2": run.get(
            "reproducibility", {}
        ).get("simulator_version")
        == "rainflow-queue-v2",
        "workflow_evaluated": run.get("workflow_state") == "EVALUATED",
        "approval_saved": run.get("approval", {}).get("status") == "approved",
        "non_baseline_policy_applied": applied_policy_id not in {None, "no_action"},
        "applied_kpi_differs_from_no_action": bool(applied)
        and bool(baseline)
        and applied != baseline,
        "required_audit_events_present": REQUIRED_AUDIT_EVENTS <= event_names,
        "all_seven_ui_states_captured": CAPTURE_STATES <= captured_states,
        "timeline_reached_20_of_20": bool(transitions)
        and transitions[-1]["current"] == 20
        and transitions[-1]["total"] == 20,
        "no_page_errors": not page_errors,
        "minimum_three_minutes_elapsed": args.fast
        or elapsed_seconds >= args.expected_duration_seconds,
    }

    release_zip = args.release_zip.resolve() if args.release_zip else None
    release_zip_sha256 = None
    if release_zip:
        if not release_zip.is_file():
            failure = failure or f"release ZIP does not exist: {release_zip}"
        else:
            release_zip_sha256 = sha256_file(release_zip)

    summary = {
        "schema_version": 1,
        "evidence_kind": "wiring_check" if args.fast else "day3_gate",
        "gate_eligible": not args.fast,
        "started_at_utc": transitions[0]["at_utc"] if transitions else None,
        "finished_at_utc": utc_now(),
        "elapsed_seconds": elapsed_seconds,
        "base_url": base_url,
        "run_id": run_id,
        "execution_git_sha": git_value(repo, "rev-parse", "HEAD"),
        "execution_git_status": git_value(repo, "status", "--short"),
        "model_freeze_git_sha": run.get("reproducibility", {}).get(
            "git_commit_sha"
        ),
        "release_zip": str(release_zip) if release_zip else None,
        "release_zip_sha256": release_zip_sha256,
        "python": sys.version,
        "platform": platform.platform(),
        "browser_channel": args.browser_channel,
        "network_policy": (
            "Playwright blocked every browser request whose host was not "
            "localhost or 127.0.0.1. This is not proof that the physical "
            "network adapter was disconnected."
        ),
        "failure": failure,
        "assertions": assertions,
        "pass": failure is None and all(assertions.values()),
    }
    write_json(output_dir / "summary.json", summary)

    manifest_lines = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            relative = path.relative_to(output_dir).as_posix()
            manifest_lines.append(f"{sha256_file(path)} *{relative}")
    (output_dir / "SHA256SUMS.txt").write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
