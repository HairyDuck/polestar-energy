# Publish checklist (maintainers)

## 1. Create the GitHub repository

```powershell
cd polestar-energy
gh auth login
gh repo create HairyDuck/polestar-energy --public --source=. --remote=origin --push --description "Home Assistant integration for Polestar Energy charge sessions (LukeDev.co.uk / HairyDuck)"
```

Or create `https://github.com/HairyDuck/polestar-energy` in the browser, then:

```powershell
git init -b main
git add .
git commit -m "Initial release: Polestar Energy Home Assistant integration"
git remote add origin https://github.com/HairyDuck/polestar-energy.git
git push -u origin main
```

## 2. Create the first release (required for HACS)

```powershell
gh release create v1.0.0 --title "v1.0.0" --notes-file CHANGELOG.md
```

Keep `custom_components/polestar_energy/manifest.json` → `version` in sync with the tag (`1.0.0` for `v1.0.0`).

## 3. Add to HACS (users)

Same pattern as [pypolestar/polestar_api](https://github.com/pypolestar/polestar_api):

1. HACS → Integrations → ⋮ → Custom repositories  
2. URL: `https://github.com/HairyDuck/polestar-energy`  
3. Category: Integration  
4. Download **Polestar Energy**, restart, then add the integration in Settings  

Until the integration is in the default HACS store, the custom-repository step is required.
## 4. Optional: default HACS store

Submit to the HACS default repository process when the project is stable:
https://hacs.xyz/docs/publish/include/

## Do not publish

- `polestar_energy_re/` (APK dumps, tokens, personal session JSON)
- FTP / HA long-lived tokens
- Any `.tokens.json` / credential files
