#!/usr/bin/env python3
"""
control_request_post.py
=======================
Sends POST requests to /api/component-emissive to make specific URDF link
components glow with defined emissive colors in the Roboreactor 3D viewer.

Usage:
    python3 control_request_post.py

The script connects to the Roboreactor server running on localhost:8095.
Edit BASE, EMAIL, and PROJECT_NAME to match your deployment.

Payload schema for POST /api/component-emissive
------------------------------------------------
{
  "email":        "<your-account-email>",
  "project_name": "<your-project-name>",
  "rules": [
    {
      "link":      "<urdf-link-name>",   # must match the link name in the URDF file
      "color":     "#rrggbb",            # CSS hex color to glow with
      "intensity": 2.0                   # emissive intensity multiplier (0 = off)
    },
    ...
  ]
}

Pass an empty "rules" list to clear all emissive highlighting for the project.

GET /api/component-emissive/latest?email=...&project_name=...
returns the currently stored rules so the viewer can poll and apply them.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error

# ── Configuration ──────────────────────────────────────────────────────────────
BASE         = "http://127.0.0.1:8095"
EMAIL        = "user@example.com"       # ← change to your account email
PROJECT_NAME = "my_robot"              # ← change to your project name
# ──────────────────────────────────────────────────────────────────────────────


def _post(path: str, payload: dict) -> dict:
    """POST JSON payload to BASE+path, return parsed JSON response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"  [HTTP {exc.code}] {body}")
        return {}
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return {}


def _get(path: str) -> dict:
    """GET BASE+path, return parsed JSON response."""
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return {}


# ── Helper ──────────────────────────────────────────────────────────────────
def set_emissive(rules: list[dict]) -> dict:
    """
    Push emissive color rules for the configured project.

    Parameters
    ----------
    rules : list of dicts
        Each dict has keys: link (str), color (str), intensity (float).
        Pass an empty list to clear all glow.

    Returns
    -------
    dict : server response
    """
    payload = {
        "email":        EMAIL,
        "project_name": PROJECT_NAME,
        "rules":        rules,
    }
    return _post("/api/component-emissive", payload)


def get_current_rules() -> dict:
    """Fetch the currently active emissive rules from the server."""
    path = (
        f"/api/component-emissive/latest"
        f"?email={urllib.parse.quote(EMAIL)}"
        f"&project_name={urllib.parse.quote(PROJECT_NAME)}"
    )
    return _get(path)


# ── Demo sequences ────────────────────────────────────────────────────────────
def demo_alert_mode() -> None:
    """Make the base link pulse red — useful for collision / alert state."""
    print("\n[1] Alert Mode: base_link → red")
    resp = set_emissive([
        {"link": "base_link",  "color": "#ff1100", "intensity": 3.0},
    ])
    print("   →", resp)


def demo_joint_highlight() -> None:
    """Highlight specific arm joints for a 'selected' visual effect."""
    print("\n[2] Joint Highlight: arm links → amber + cyan")
    resp = set_emissive([
        {"link": "arm_link_1", "color": "#ffaa00", "intensity": 2.0},
        {"link": "arm_link_2", "color": "#ffaa00", "intensity": 2.0},
        {"link": "wrist_link", "color": "#00ffdd", "intensity": 2.5},
    ])
    print("   →", resp)


def demo_full_robot_scan() -> None:
    """Give every tracked link a unique color for a 'system scan' look."""
    print("\n[3] Full Scan: rainbow link colors")
    resp = set_emissive([
        {"link": "base_link",     "color": "#ff0055", "intensity": 1.8},
        {"link": "torso_link",    "color": "#ff8800", "intensity": 1.8},
        {"link": "head_link",     "color": "#ffff00", "intensity": 1.8},
        {"link": "arm_link_1",    "color": "#00ff88", "intensity": 1.8},
        {"link": "arm_link_2",    "color": "#00aaff", "intensity": 1.8},
        {"link": "gripper_link",  "color": "#8800ff", "intensity": 1.8},
    ])
    print("   →", resp)


def demo_clear() -> None:
    """Remove all emissive highlighting."""
    print("\n[4] Clear all emissive glow")
    resp = set_emissive([])
    print("   →", resp)


def demo_custom(link: str, color: str, intensity: float = 2.0) -> None:
    """
    Highlight a single named URDF link.

    Parameters
    ----------
    link      : URDF link name (e.g. "base_link", "turret_link")
    color     : hex color string (e.g. "#00ff88")
    intensity : emissive strength, default 2.0
    """
    print(f"\n[Custom] {link!r} → {color} (intensity={intensity})")
    resp = set_emissive([{"link": link, "color": color, "intensity": intensity}])
    print("   →", resp)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import urllib.parse  # needed by get_current_rules

    print("=" * 60)
    print("Roboreactor Component Emissive Control")
    print(f"  Server  : {BASE}")
    print(f"  Email   : {EMAIL}")
    print(f"  Project : {PROJECT_NAME}")
    print("=" * 60)

    # --- Show current rules ---
    print("\n[0] Current emissive rules:")
    print("   →", get_current_rules())

    # --- Run demo sequences with a short pause between each ---
    demo_alert_mode()
    time.sleep(3)

    demo_joint_highlight()
    time.sleep(3)

    demo_full_robot_scan()
    time.sleep(4)

    demo_clear()

    print("\n[Done] All sequences complete.")
    print(
        "\nTo highlight a custom link, call:\n"
        "    demo_custom('your_link_name', '#00ff88', intensity=2.5)\n"
        "or POST directly to /api/component-emissive with your rules payload."
    )
