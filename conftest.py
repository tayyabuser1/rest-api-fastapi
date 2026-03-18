"""
Pytest configuration and shared fixtures
"""

import pytest
import logging
import json
from datetime import datetime


# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_session_setup():
    """Setup for entire test session"""
    logger.info("="*70)
    logger.info("TEST SESSION STARTED")
    logger.info("="*70)
    yield
    logger.info("="*70)
    logger.info("TEST SESSION COMPLETED")
    logger.info("="*70)


def pytest_configure(config):
    """Pytest configuration hook"""
    logger.info(f"Running tests with {config.option.verbose} verbosity")


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection"""
    for item in items:
        # Add markers based on test name
        if "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        if "slow" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def test_data():
    """Provide test data"""
    return {
        'users': [
            {'name': 'Test User 1', 'email': 'test1@example.com'},
            {'name': 'Test User 2', 'email': 'test2@example.com'},
            {'name': 'Test User 3', 'email': 'test3@example.com'},
        ]
    }


@pytest.fixture
def json_report(tmp_path):
    """Create JSON report path"""
    report_file = tmp_path / "test_report.json"
    return report_file


def pytest_runtest_logreport(report):
    """Log test results after each test"""
    if report.when == "call":
        if report.outcome == "passed":
            logger.info(f"✓ {report.nodeid} PASSED")
        elif report.outcome == "failed":
            logger.error(f"✗ {report.nodeid} FAILED")
        elif report.outcome == "skipped":
            logger.warning(f"⊝ {report.nodeid} SKIPPED")


@pytest.fixture
def benchmark_data():
    """Provide benchmark data"""
    return {
        'max_execution_time': 0.1,  # 100ms
        'target_success_rate': 95.0,  # 95%
    }
