import os

import httpx

import gh_util
from gh_util.logging import get_logger

logger = get_logger(__name__)


class GHClient(httpx.AsyncClient):
    """A wrapper around httpx.AsyncClient that adds GitHub authentication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_authentication()

    def _set_authentication(self):
        if gh_util.settings.token:
            token = gh_util.settings.token.get_secret_value()
            logger.info_kv("AUTH", "Using token from settings `GH_UTIL_TOKEN`", "green")
        elif token := os.getenv("GITHUB_TOKEN"):
            logger.info_kv("AUTH", "Using token from env vars `GITHUB_TOKEN`", "green")
        else:
            logger.warning_kv(
                "AUTH",
                (
                    "`GH_UTIL_TOKEN` not set in env vars or `.env` - watch out for rate limits and 401s!"
                    " see https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token"
                ),
                "red",
            )
            token = None

        if token:
            self.headers.update(
                {
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": f"token {token}",
                }
            )

    async def request(self, method, url, *args, **kwargs) -> httpx.Response:
        """Allow passing a path relative to `GH_UTIL_BASE_URL`."""
        url = str(url)
        if url.startswith("/"):
            url = f"{gh_util.settings.base_url}{url}"

        response = await super().request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response
