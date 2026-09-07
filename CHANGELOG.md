# Changelog

## 1.0.2 – 2026-09-07

- Remove helper scripts from the public repo
- Branding is HairyDuck only

## 1.0.1 – 2026-09-07

- Use the Polestar Energy app orange icon for brand assets
- Device manufacturer shown as HairyDuck (unofficial; not Polestar / Jedlix)

## 1.0.0 – 2026-09-07

- Initial public release (HairyDuck)
- Auth0 PKCE login via Polestar ID email and password
- Session history from Jedlix mobile gateway (`/sessions`, `/addresses`, `/vehicles`)
- Sensors: last session energy/cost/savings/start/end/location, energy today/month
- Binary sensors: session active, charging at home (active home session only)
- Config flow: Polestar ID email + password (no redirect paste / phone required)
- Config flow reauth support
- HACS-ready: `hacs.json`, brand icons under `brand/`, hassfest + HACS GitHub Actions
