# Polestar Energy

This application is not an official app affiliated with Polestar or Jedlix.

A [LukeDev.co.uk](https://lukedev.co.uk/) / [HairyDuck](https://github.com/HairyDuck) Home Assistant integration for **Polestar Energy** charge sessions (energy used, session times, home vs away).

This is **separate** from the car telemetry integration [pypolestar/polestar_api](https://github.com/pypolestar/polestar_api) (battery, location, odometer, and so on). Use that for the car. Use **this** for charge-session data from the Polestar Energy / Jedlix smart-charging app.

N.B. Cost and savings values from the app are **indicative only**. Prefer your wallbox / electricity meter sensors for billing. The underlying API is unofficial and may change when the mobile app is updated.

This integration is brand new, so time will tell how it holds up as Polestar / Jedlix change things. Issues, pull requests, and testing help are very welcome; please feel free to chip in.

## Screenshots

### Setup

Enter your Polestar ID email and password:

![Polestar Energy setup](images/setup.png)

### Device

![Polestar Energy device](images/device.png)

### Result

![Polestar Energy result card](images/result.png)

### Entities

![Polestar Energy entities](images/entities.png)

## Use your Polestar account

Use the same Polestar ID email and password you use in the Polestar Energy app (and in [Polestar API](https://github.com/pypolestar/polestar_api)). You can check login here: https://polestarid.eu.polestar.com/Account/login

## Prerequisites

* HACS (Home Assistant Community Store) must be installed. If you have not installed HACS yet, follow the [official HACS installation guide](https://hacs.xyz/docs/use/#getting-started-with-hacs).

## Add in HA Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=HairyDuck&repository=polestar-energy&category=integration)

### Custom repository (until listed in HACS by default)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Repository: `https://github.com/HairyDuck/polestar-energy`
3. Category: **Integration**
4. Download **Polestar Energy**
5. Restart Home Assistant
6. Settings → Devices & services → **Add integration** → **Polestar Energy**

### Fill the information

Enter your **Polestar ID email** and **password**. Home Assistant signs in for you; no phone, USB cable, or copying redirect links.

Only OAuth tokens are stored afterwards (not your password). Tokens refresh automatically.

## What you get

* Last session energy (kWh), start/end, location
* Last session cost / savings from the app (indicative)
* Energy today / this month from session history
* Binary: session active
* Binary: charging at home (active session at a configured home address)

## Manual install

Clone or copy this repository and copy the folder `custom_components/polestar_energy` into your Home Assistant `custom_components` directory, then restart and add the integration as above.

## Support

* Issues: https://github.com/HairyDuck/polestar-energy/issues
* Contributions: see [CONTRIBUTING.md](CONTRIBUTING.md)
* Author: [HairyDuck](https://github.com/HairyDuck) · [LukeDev.co.uk](https://lukedev.co.uk/)

## License

MIT – see [LICENSE](LICENSE).
