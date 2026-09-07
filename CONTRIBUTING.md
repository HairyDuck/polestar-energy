# Contributing

Thanks for helping improve this LukeDev / HairyDuck Home Assistant integration.

## Development layout

```
polestar-energy/
├── custom_components/polestar_energy/   # the integration
├── hacs.json
├── README.md
└── LICENSE
```

Copy `custom_components/polestar_energy` into a Home Assistant `config/custom_components/` folder (or symlink it) and restart.

## Guidelines

- Keep the integration **read-only** for charge sessions (no smart-charging controls unless explicitly designed and documented).
- Do not commit tokens, passwords, APK dumps, or personal session JSON.
- Prefer clear UK English in user-facing strings.
- Match existing Home Assistant patterns (config flow, coordinator, entity naming).

## Pull requests

1. Fork the repo and create a branch.
2. Make a focused change.
3. Update `README.md` / `CHANGELOG.md` when behaviour changes.
4. Open a PR against `main`.

## Releases (maintainers)

HACS picks up GitHub releases. Tag semantic versions (`v1.0.1`) and keep `manifest.json` `version` in sync.
