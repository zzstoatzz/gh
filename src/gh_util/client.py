import httpx

import gh_util
from gh_util.logging import get_logger

logger = get_logger(__name__)


class GHClient(httpx.AsyncClient):
    """A wrapper around httpx.AsyncClient that adds GitHub authentication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if gh_util.settings.token:
            logger.debug_kv(
                "AUTH",
                "Using GitHub token set in environment via `GH_UTIL_TOKEN`",
                "blue",
            )
            self.headers[
                "Authorization"
            ] = f"token {gh_util.settings.token.get_secret_value()}"
        else:
            logger.warning_kv(
                "AUTH",
                "`GH_UTIL_TOKEN` not set in environment - watch out for rate limits!",
                "red",
            )
        self.headers["Accept"] = "application/vnd.github.v3+json"

    async def request(self, method, url, *args, **kwargs) -> httpx.Response:
        """Allow passing in a relative URL."""
        url = str(url)
        if url.startswith("/"):
            url = f"{gh_util.settings.base_url}{url}"

        response = await super().request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response
