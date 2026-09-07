# Publish checklist (maintainers)

## Why GitHub Actions?

**Yes, you need them** if you want the integration in the [default HACS store](https://www.hacs.xyz/docs/publish/include/). HACS requires both workflows to pass **with no ignored checks**, then a real GitHub **release** (not just a tag):

| Workflow | Action | Purpose |
| --- | --- | --- |
| Hassfest | `home-assistant/actions/hassfest` | Validates the custom component (manifest, config flow, structure) |
| HACS | `hacs/action` with `category: integration` | Same checks HACS uses when validating a repository |

For **custom-repository** install only, Actions are optional but still strongly recommended so regressions are caught on every push/PR. This repo already has `.github/workflows/validate.yml` (push, PR, daily schedule, manual dispatch).

## 1. Create the GitHub repository

```powershell
cd polestar-energy
gh auth login
gh repo create HairyDuck/polestar-energy --public --source=. --remote=origin --push --description "Home Assistant integration for Polestar Energy charge sessions (LukeDev.co.uk / HairyDuck)"
```

Or create `https://github.com/HairyDuck/polestar-energy` in the browser, then push `main`.

### Repository settings HACS expects

After create, set these on GitHub (checked when submitting to `hacs/default`):

* **Description** filled in
* **Topics**, e.g. `home-assistant`, `hacs`, `polestar`, `custom-component`
* **Issues** enabled
* Brand icons present under `custom_components/polestar_energy/brand/` (`icon.png` minimum)

## 2. Confirm Actions pass

Push `main`, open the Actions tab, and ensure **Hassfest validation** and **HACS validation** are green. Do not use `ignore:` in the HACS action.

## 3. Create the first release (required for default HACS)

```powershell
gh release create v1.0.0 --title "v1.0.0" --notes-file CHANGELOG.md
```

Keep `custom_components/polestar_energy/manifest.json` → `version` in sync with the tag (`1.0.0` for `v1.0.0`).

## 4. Add to HACS (users)

Same pattern as [pypolestar/polestar_api](https://github.com/pypolestar/polestar_api):

1. HACS → Integrations → ⋮ → Custom repositories  
2. URL: `https://github.com/HairyDuck/polestar-energy`  
3. Category: Integration  
4. Download **Polestar Energy**, restart, then add the integration in Settings  

Until the integration is in the default HACS store, the custom-repository step is required.

## 5. Optional: default HACS store

When stable and Actions + a release are green:

https://hacs.xyz/docs/publish/include/

## Do not publish

* `polestar_energy_re/` (APK dumps, tokens, personal session JSON)
* FTP / HA long-lived tokens
* Any `.tokens.json` / credential files
