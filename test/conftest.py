import os
import shutil
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import TypeVar
from zipfile import ZipFile

import pytest
import requests

_XFAIL_LIST = os.getenv("GHA_SIGSTORE_CONFORMANCE_XFAIL", "").split()


class OidcTokenError(Exception):
    pass


class ConfigError(Exception):
    pass


def pytest_addoption(parser) -> None:
    """
    Add the `--entrypoint`, `--github-token`, and `--skip-signing` flags to
    the `pytest` CLI.
    """
    parser.addoption(
        "--entrypoint",
        action="store",
        help="the command to invoke the Sigstore client under test",
        required=True,
        type=str,
    )
    parser.addoption(
        "--github-token",
        action="store",
        help="the GitHub token to supply to the Sigstore client under test",
        type=str,
    )
    parser.addoption(
        "--skip-signing",
        action="store_true",
        help="skip tests that require signing functionality",
    )


def pytest_runtest_setup(item):
    if "signing" in item.keywords and item.config.getoption("--skip-signing"):
        pytest.skip("skipping test that requires signing support due to `--skip-signing` flag")


def pytest_configure(config):
    if not config.getoption("--github-token") and not config.getoption("--skip-signing"):
        raise ConfigError("Please specify one of '--github-token' or '--skip-signing'")

    config.addinivalue_line("markers", "signing: mark test as requiring signing functionality")


def pytest_internalerror(excrepr, excinfo):
    if excinfo.type == ConfigError:
        print(excinfo.value)
        return True

    return False


@pytest.fixture(autouse=True)
def workspace():
    """
    Create a temporary workspace directory to perform the test in.
    """
    workspace = tempfile.TemporaryDirectory()

    # Move entire contents of artifacts directory into workspace
    assets_dir = Path(__file__).parent.parent / "test" / "assets"
    shutil.copytree(assets_dir, workspace.name, dirs_exist_ok=True)

    # Now change the current working directory to our workspace
    os.chdir(workspace.name)

    yield Path(workspace.name)
    workspace.cleanup()


@pytest.fixture(autouse=True)
def conformance_xfail(request):
    if request.node.originalname in _XFAIL_LIST:
        request.node.add_marker(pytest.mark.xfail(reason="skipped by suite runner", strict=True))
