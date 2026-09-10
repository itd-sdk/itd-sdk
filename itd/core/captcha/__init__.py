from typing import TYPE_CHECKING

# from itd.api.auth import get_captcha_provider
# from itd.core.captcha import cloudflare, itd  # required to they fill "providers" value # noqa
# from itd.core.captcha.base import providers
from itd.core.captcha.base import CAPTCHA_AVAILABLE
from itd.core.captcha.cloudflare import CloudflareProvider
from itd.core.logger import get_logger, iprint, rich_input

if TYPE_CHECKING:
    from itd.core.client import Client

l = get_logger('captcha')


def get_turnstile(client: 'Client | None' = None, status=None) -> str:  # tuple[str, str]:
    # provider_data = {'provider': 'cloudflare', 'token': 'turnstileToken'}  # get_captcha_provider(client)
    # if provider_data['provider'] not in providers:
    #     raise RuntimeError(f'Unknown provider: {provider_data["provider"]}')

    # provider = providers[provider_data['provider']]()
    if client and not client.config.captcha_solve:
        l.warning('captcha solving disabled')
        iprint(l, 'solve captcha on other devices via `uv run itd captcha`, then paste result here')
        iprint(l, 'enter `continue` to force solve captcha on this device')
        if status:
            status.stop()
        turnstile = rich_input('turnstile', 'yellow')
        if turnstile != 'continue':
            return turnstile
        if status:
            status.start()

    if not CAPTCHA_AVAILABLE:
        l.error(r'captcha libraries not installed; install via `uv add itd-sdk\[captcha]`')
    provider = CloudflareProvider(False if not client else client.config.captcha_headless)
    provider.launch()
    turnstile = provider.solve()
    provider.close()

    return turnstile  # provider_data.get('token', 'token'), turnstile
