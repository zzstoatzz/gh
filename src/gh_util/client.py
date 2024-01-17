import httpx

import gh_util


class GHClient(httpx.AsyncClient):
    """A wrapper around httpx.AsyncClient that adds GitHub authentication."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if gh_util.settings.token:
            self.headers[
                "Authorization"
            ] = f"token {gh_util.settings.token.get_secret_value()}"
        self.headers["Accept"] = "application/vnd.github.v3+json"

    async def request(self, method, url, *args, **kwargs) -> httpx.Response:
        """Allow passing in a relative URL."""
        url = str(url)
        if url.startswith("/"):
            url = f"{gh_util.settings.base_url}{url}"

        response = await super().request(method, url, *args, **kwargs)
        response.raise_for_status()
        return response
