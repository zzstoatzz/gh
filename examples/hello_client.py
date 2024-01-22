from gh_util.client import GHClient
from gh_util.types import GitHubUser
from jinja2 import Template


async def get_current_user() -> GitHubUser:
    async with GHClient() as client:
        response = await client.get("/user")
        return GitHubUser.model_validate(response.json())


if __name__ == "__main__":
    import asyncio

    print(
        Template(
            """
            In the vibrant digital landscape of GitHub, a figure emerges: {{ user.login }}.
            {% if user.location %}Hailing from the bustling streets of {{ user.location }}, {% endif %}
            {% if user.company %}this maestro of code aligns with {{ user.company.strip() }}, {% endif %}
            scripting the future.
            {% if user.bio %}Hark! Their story is riveting: '{{ user.bio }}'.{% endif %}
            {% if user.blog %}The chronicles of {{ user.login }} unfold at {{ user.blog }}, an odyssey of innovation and discovery.{% else %}The chronicles of {{ user.login }} unfold in the digital realm, marking a journey of innovation and discovery.{% endif %}
        """
        ).render(user=asyncio.run(get_current_user()))
    )
