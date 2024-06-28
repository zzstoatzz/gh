import pytest
import asyncio

@pytest.fixture
async def gh_util_setup():
    # Setup code for gh_util tests
    yield
    # Teardown code for gh_util tests

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
