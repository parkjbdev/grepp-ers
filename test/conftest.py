import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    config.inicfg["asyncio_default_fixture_loop_scope"] = "module"
