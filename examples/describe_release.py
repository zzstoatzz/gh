import tempfile
import webbrowser

from gh_util.functions import describe_latest_release
from jinja2 import Template

custom_template = Template(
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ repo }} {{ release.name }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .content { white-space: pre-wrap; } /* Preserves whitespace and line breaks */
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ repo }} {{ release.name }}</h1>
        <p><strong>Tag:</strong> {{ release.tag_name }}</p>
        <p><strong>Published:</strong> {{ release.published_at.strftime("%A, %d %B %Y %H:%M:%S %Z") }}</p>
        <div class="content">{{ release.body }}</div>
        <p><a href="{{ release.html_url }}">View on GitHub</a></p>
    </div>
</body>
</html>
"""
)


async def main(owner: str, repo: str) -> None:
    result = await describe_latest_release(owner, repo, custom_template)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(result)
        filepath = f.name

        webbrowser.open(f"file://{filepath}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main("prefecthq", "marvin"))
