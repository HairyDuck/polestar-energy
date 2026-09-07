# Polestar Energy – Home Assistant integration

This is a custom component to get **Polestar Energy** charge-session information into [Home Assistant](https://home-assistant.io).

Built by [HairyDuck](https://github.com/HairyDuck).

Not affiliated with Polestar or Jedlix. Complementary to [pypolestar/polestar_api](https://github.com/pypolestar/polestar_api) (car data), not a replacement for it.

## Installation

### Install using HACS (recommended)

If you do not have HACS installed yet, visit https://hacs.xyz for installation instructions.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=HairyDuck&repository=polestar-energy&category=integration)

1. Download **Polestar Energy** in HACS
2. Restart Home Assistant
3. Add the integration:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=polestar_energy)

Or manually: HACS → Integrations → ⋮ → **Custom repositories** → add `https://github.com/HairyDuck/polestar-energy` as **Integration**.

### Install manually

Clone or copy this repository and copy the folder `custom_components/polestar_energy` into `/config/custom_components/`.

## Configuration

Once installed, configure via **Settings → Devices & services → Add integration → Polestar Energy**.

Enter your Polestar ID email and password (same as the Polestar Energy app). No phone or redirect links required.

![Setup](images/setup.png)

![Device](images/device.png)

![Entities](images/result.png)
