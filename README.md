# Polestar Energy for Home Assistant

[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![GitHub release](https://img.shields.io/github/v/release/HairyDuck/polestar-energy?include_prereleases)](https://github.com/HairyDuck/polestar-energy/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.8%2B-blue.svg)](https://www.home-assistant.io/)
[![LukeDev](https://img.shields.io/badge/LukeDev.co.uk-HairyDuck-111111.svg)](https://lukedev.co.uk/)

Unofficial Home Assistant integration for **Polestar Energy** charge sessions.

Built by [LukeDev.co.uk](https://lukedev.co.uk/) / [HairyDuck](https://github.com/HairyDuck).

> **Not affiliated with Polestar or Jedlix.** This uses the same consumer APIs as the Polestar Energy mobile app. The API can change without notice.

This is **not** the car telemetry integration ([pypolestar/polestar_api](https://github.com/pypolestar/polestar_api)). Use that for battery, location, and climate. Use **this** for charge-session history from the Polestar Energy / Jedlix smart-charging app.

---

## What you get

| Entity | Meaning |
| --- | --- |
| Last session energy | kWh from the most recent charge session |
| Last session cost / savings | Figures from the app (indicative only) |
| Last session start / end | Timestamps |
| Last session location | Address / place name for that session |
| Energy today / this month | Summed from session history |
| Session active | A charge session is in progress |
| Charging at home | An **active** session is at a configured home address |

Recent sessions are also exposed as attributes on the last-session sensors (handy for dashboards and automations).

### Costs are not gospel

App cost and savings values are useful for rough comparison, but treat your wallbox meter and energy tariff sensors as the source of truth for billing.

---

## Install with HACS (recommended)

1. Open **HACS** → **Integrations** → ⋮ → **Custom repositories**.
2. Add:
   - Repository: `https://github.com/HairyDuck/polestar-energy`
   - Category: **Integration**
3. Click **Add**, then find **Polestar Energy** and install it.
4. Restart Home Assistant.
5. Go to **Settings** → **Devices & services** → **Add integration** → **Polestar Energy**.

### Manual install

1. Copy `custom_components/polestar_energy` into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. Add the integration as above.

---

## Setup (Polestar ID login)

The integration uses the same Polestar ID sign-in as the phone app (Auth0 + PKCE).

1. When you add the integration, Home Assistant shows a **login URL**.
2. Open that URL in a browser on your phone or computer.
3. Sign in with the **same Polestar ID** used in the Polestar Energy app.
4. After login, the browser tries to open an app link starting with:
   `com.polestar.smartcharging://…`
5. Copy that **full URL** from the address bar (or from the “open in app” prompt) and paste it into the Home Assistant form.
6. Submit. Tokens are stored in your config entry and refreshed automatically.

If login fails later, use **Reconfigure** / re-add and paste a fresh redirect URL.

---

## Example uses

- Track whether a session is **at home or away** (`binary_sensor.polestar_energy_charging_at_home` while a session is active).
- Drive automations when a session starts or finishes.
- Cross-check session kWh against your home charger energy sensors.
- Show last session location on a dashboard card.

---

## Requirements

- Home Assistant **2024.8** or newer
- A Polestar Energy account (Jedlix-backed) that already works in the mobile app
- Outbound HTTPS to:
  - `jedlix-b2b.eu.auth0.com`
  - `polestarid.eu.polestar.com` (during login)
  - `mobilegateway.jedlix.com`

---

## Support

- Issues: [GitHub Issues](https://github.com/HairyDuck/polestar-energy/issues)
- Author: [HairyDuck](https://github.com/HairyDuck) · [LukeDev.co.uk](https://lukedev.co.uk/)

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Disclaimer

This project is unofficial and open source under the [MIT License](LICENSE). Polestar, Jedlix, and related marks belong to their respective owners. Use at your own risk; cloud APIs may break when the app is updated.
