"""
Shared fixtures for SmartTrader tests
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope='session')
def project_root_path():
    """Return the project root path"""
    return project_root


@pytest.fixture(scope='function')
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests"""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir
