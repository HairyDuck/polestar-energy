"""Constants for the Polestar Energy integration."""

DOMAIN = "polestar_energy"

CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EXPIRES_AT = "expires_at"
CONF_USER_ID = "user_id"
CONF_HOME_LOCATION_IDS = "home_location_ids"
CONF_HOME_LOCATION_NAMES = "home_location_names"

# From Polestar Energy Android app 7.1.0 (com.polestar.smartcharging)
AUTH0_DOMAIN = "jedlix-b2b.eu.auth0.com"
AUTH0_CLIENT_ID = "IbeiO6vFRsy37rdrN7tsX1mEenYCwvSL"
AUTH0_CONNECTION = "polestar"
AUTH0_AUDIENCE = "https://jedlix-b2b/"
AUTH0_SCOPE = "openid offline_access profile email"
AUTH_REDIRECT_URI = (
    "com.polestar.smartcharging://jedlix-b2b.eu.auth0.com"
    "/android/com.polestar.smartcharging/callback"
)

API_KEY = "9cb19e6c885983102a4bc9e096acea8b"
MOBILE_GATEWAY_BASE = "https://mobilegateway.jedlix.com/v1/api"
CLIENT_NAME = "LukeDev-PolestarEnergy"
CLIENT_VERSION = "1.0.0"

DEFAULT_SCAN_INTERVAL_SECONDS = 300

# Prefer Jedlix uuid claim over Auth0 external Polestar account id in `sub`.
USER_ID_CLAIM_CANDIDATES = (
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/uuid",
    "https://jedlix.com/user_id",
    "https://schemas.jedlix.com/user_id",
    "user_id",
    "userId",
    "sub",
)
