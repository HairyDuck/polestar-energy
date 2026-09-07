"""Render HA-style README screenshots from live entity states."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import urllib.request
from playwright.async_api import async_playwright

import os

TOKEN = os.environ.get("HA_TOKEN", "")
BASE = os.environ.get("HA_URL", "http://homeassistant.local:8123")
OUT = Path(__file__).resolve().parents[1] / "images"
OUT.mkdir(parents=True, exist_ok=True)

ENTITY_IDS = [
    "sensor.polestar_energy_last_session_energy",
    "sensor.polestar_energy_last_session_cost",
    "sensor.polestar_energy_last_session_savings",
    "sensor.polestar_energy_last_session_start",
    "sensor.polestar_energy_last_session_end",
    "sensor.polestar_energy_last_session_location",
    "sensor.polestar_energy_energy_today",
    "sensor.polestar_energy_energy_this_month",
    "binary_sensor.polestar_energy_session_active",
    "binary_sensor.polestar_energy_charging_at_home",
]


def api_get(path: str):
    req = urllib.request.Request(
        f"{BASE}{path}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def friendly(state: dict) -> str:
    return state.get("attributes", {}).get("friendly_name") or state["entity_id"]


def display_state(state: dict) -> str:
    value = state.get("state")
    attrs = state.get("attributes") or {}
    unit = attrs.get("unit_of_measurement")
    if "location" in state["entity_id"]:
        return "Home charging location"
    if value in ("on", "off") and state["entity_id"].startswith("binary_sensor"):
        return "On" if value == "on" else "Off"
    if unit:
        # Round long monetary values for cleaner screenshots
        try:
            if unit == "GBP":
                return f"{float(value):.2f} {unit}"
        except (TypeError, ValueError):
            pass
        return f"{value} {unit}"
    if "T" in str(value) and "+" in str(value):
        return str(value).replace("T", " ")[:19]
    return str(value)


def build_entities_html(states: list[dict]) -> str:
    rows = []
    for st in states:
        rows.append(
            f"""
            <div class="row">
              <div class="icon">⚡</div>
              <div class="meta">
                <div class="name">{friendly(st)}</div>
                <div class="id">{st['entity_id']}</div>
              </div>
              <div class="value">{display_state(st)}</div>
            </div>"""
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/>
<style>
  html,body {{ margin:0; background:#f2f4f6; font-family: Roboto, "Segoe UI", sans-serif; color:#212121; }}
  .wrap {{ padding:28px; }}
  .card {{
    max-width: 720px; margin:0 auto; background:#fff; border-radius:12px;
    box-shadow: 0 2px 6px rgba(0,0,0,.12); overflow:hidden;
  }}
  .header {{
    padding:18px 20px; border-bottom:1px solid #eee; display:flex; align-items:center; gap:12px;
  }}
  .badge {{
    width:40px; height:40px; border-radius:50%; background:#03a9f4; color:#fff;
    display:flex; align-items:center; justify-content:center; font-weight:700;
  }}
  .title {{ font-size:18px; font-weight:500; }}
  .subtitle {{ font-size:13px; color:#666; }}
  .row {{
    display:flex; align-items:center; gap:14px; padding:14px 20px; border-bottom:1px solid #f0f0f0;
  }}
  .row:last-child {{ border-bottom:none; }}
  .icon {{ width:28px; text-align:center; opacity:.7; }}
  .meta {{ flex:1; min-width:0; }}
  .name {{ font-size:15px; }}
  .id {{ font-size:12px; color:#888; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .value {{ font-size:15px; color:#03a9f4; font-weight:500; white-space:nowrap; }}
  .footer {{ padding:12px 20px; font-size:12px; color:#888; background:#fafafa; }}
</style></head>
<body><div class="wrap"><div class="card">
  <div class="header">
    <div class="badge">PE</div>
    <div>
      <div class="title">Polestar Energy</div>
      <div class="subtitle">LukeDev.co.uk / HairyDuck · charge sessions</div>
    </div>
  </div>
  {''.join(rows)}
  <div class="footer">Unofficial integration · app costs are indicative only</div>
</div></div></body></html>"""


def build_setup_html() -> str:
    return """<!doctype html>
<html><head><meta charset="utf-8"/>
<style>
  html,body { margin:0; background:#f2f4f6; font-family: Roboto, "Segoe UI", sans-serif; color:#212121; }
  .wrap { padding:40px; }
  .dialog {
    max-width: 560px; margin:0 auto; background:#fff; border-radius:12px;
    box-shadow: 0 8px 24px rgba(0,0,0,.16); overflow:hidden;
  }
  .bar { height:4px; background:#03a9f4; }
  .body { padding:24px 28px 8px; }
  h1 { margin:0 0 8px; font-size:22px; font-weight:500; }
  p { margin:0 0 14px; color:#555; line-height:1.45; font-size:14px; }
  ol { margin:0 0 16px; padding-left:20px; color:#444; font-size:14px; line-height:1.5; }
  .field { margin:18px 0; }
  .label { font-size:12px; color:#03a9f4; margin-bottom:4px; }
  .input {
    border:none; border-bottom:2px solid #03a9f4; width:100%; padding:10px 0;
    font-size:15px; color:#333; background:transparent;
  }
  .hint { font-size:12px; color:#888; margin-top:6px; }
  .actions { display:flex; justify-content:flex-end; gap:8px; padding:16px 20px 20px; }
  .btn { border:none; background:transparent; color:#03a9f4; font-weight:600; padding:10px 14px; cursor:default; }
  .btn.primary { background:#03a9f4; color:#fff; border-radius:6px; }
  code { background:#f5f5f5; padding:1px 5px; border-radius:4px; font-size:12px; }
</style></head>
<body><div class="wrap"><div class="dialog"><div class="bar"></div>
  <div class="body">
    <h1>Polestar Energy</h1>
    <p>Sign in with the same Polestar ID email and password you use in the Polestar Energy app. No phone or redirect links needed.</p>
    <div class="field">
      <div class="label">Polestar ID email</div>
      <div class="input">you@example.com</div>
    </div>
    <div class="field" style="margin-top:18px">
      <div class="label">Password</div>
      <div class="input">••••••••••••</div>
    </div>
    <div class="field" style="margin-top:18px">
      <div class="label">Name</div>
      <div class="input">Polestar Energy</div>
    </div>
  </div>
  <div class="actions">
    <div class="btn">CANCEL</div>
    <div class="btn primary">SUBMIT</div>
  </div>
</div></div></body></html>"""


async def render(html: str, filename: str, width: int = 900, height: int = 900) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
        )
        await page.set_content(html, wait_until="load")
        card = page.locator(".card, .dialog").first
        await card.screenshot(path=str(OUT / filename))
        print("wrote", OUT / filename)
        await browser.close()


async def main() -> None:
    await render(build_setup_html(), "setup.png", width=800, height=700)
    if not TOKEN:
        print("HA_TOKEN not set; skipped entities.png / result.png")
        return
    states = []
    for eid in ENTITY_IDS:
        try:
            states.append(api_get(f"/api/states/{eid}"))
        except Exception as err:
            print("skip", eid, err)
    await render(build_entities_html(states), "entities.png", height=1100)

    # Compact "result" card: key sensors only
    key_ids = {
        "sensor.polestar_energy_last_session_energy",
        "sensor.polestar_energy_last_session_location",
        "sensor.polestar_energy_energy_today",
        "sensor.polestar_energy_energy_this_month",
        "binary_sensor.polestar_energy_session_active",
        "binary_sensor.polestar_energy_charging_at_home",
    }
    key_states = [s for s in states if s["entity_id"] in key_ids]
    await render(build_entities_html(key_states), "result.png", height=780)


if __name__ == "__main__":
    asyncio.run(main())
