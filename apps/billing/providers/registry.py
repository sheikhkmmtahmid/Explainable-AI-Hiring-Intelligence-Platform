from .manual_provider import ManualProvider
from .sslcommerz_provider import SSLCommerzProvider
from .stripe_provider import StripeProvider

_PROVIDERS = {
    "stripe": StripeProvider(),
    "sslcommerz": SSLCommerzProvider(),
    "manual": ManualProvider(),
}


def get_provider(code: str):
    provider = _PROVIDERS.get(code)
    if provider is None:
        raise ValueError(f"Unknown payment provider code: {code!r}")
    return provider
