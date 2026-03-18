"""
Professional Automation Testing Framework
- Comprehensive test suite structure
- Fixtures and conftest setup
- Test reporting and analytics
- Performance testing
- Data-driven testing
"""

import pytest
import time
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestMetrics:
    """Test execution metrics"""
    test_name: str
    duration: float
    status: TestStatus
    memory_usage: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error_message: str = ""


@dataclass
class TestResult:
    """Complete test result"""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total_duration: float = 0.0
    metrics: List[TestMetrics] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""


class SampleApplication:
    """Sample application for testing"""
    
    def __init__(self):
        self.users = {}
        self.counter = 0
    
    def add_user(self, name: str, email: str) -> Dict:
        """Add a user"""
        if not name or not email:
            raise ValueError("Name and email are required")
        
        self.counter += 1
        user = {
            'id': self.counter,
            'name': name,
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        self.users[self.counter] = user
        return user
    
    def get_user(self, user_id: int) -> Dict:
        """Get user by ID"""
        if user_id not in self.users:
            raise KeyError(f"User {user_id} not found")
        return self.users[user_id]
    
    def update_user(self, user_id: int, **kwargs) -> Dict:
        """Update user details"""
        user = self.get_user(user_id)
        user.update(kwargs)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def list_users(self) -> List[Dict]:
        """List all users"""
        return list(self.users.values())
    
    def get_user_count(self) -> int:
        """Get total user count"""
        return len(self.users)


class PerformanceTester:
    """Performance testing utilities"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> tuple:
        """Measure function execution time"""
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
    
    @staticmethod
    def stress_test(func, iterations: int, *args, **kwargs) -> Dict:
        """Run stress test"""
        times = []
        for _ in range(iterations):
            start = time.time()
            func(*args, **kwargs)
            times.append(time.time() - start)
        
        return {
            'iterations': iterations,
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times)
        }


class TestReporter:
    """Test result reporting"""
    
    def __init__(self):
        self.results = TestResult()
        self.metrics: List[TestMetrics] = []
    
    def add_metric(self, metric: TestMetrics) -> None:
        """Add test metric"""
        self.metrics.append(metric)
        
        if metric.status == TestStatus.PASSED:
            self.results.passed += 1
        elif metric.status == TestStatus.FAILED:
            self.results.failed += 1
        elif metric.status == TestStatus.SKIPPED:
            self.results.skipped += 1
        
        self.results.total_duration += metric.duration
    
    def generate_report(self) -> Dict:
        """Generate test report"""
        self.results.end_time = datetime.now().isoformat()
        self.results.total_tests = len(self.metrics)
        self.results.metrics = self.metrics
        
        report = {
            'summary': {
                'total_tests': self.results.total_tests,
                'passed': self.results.passed,
                'failed': self.results.failed,
                'skipped': self.results.skipped,
                'success_rate': (self.results.passed / self.results.total_tests * 100) if self.results.total_tests > 0 else 0,
                'total_duration': self.results.total_duration
            },
            'metrics': [asdict(m) for m in self.metrics]
        }
        
        return report
    
    def print_report(self) -> None:
        """Print formatted report"""
        report = self.generate_report()
        summary = report['summary']
        
        print("\n" + "="*70)
        print("TEST EXECUTION REPORT")
        print("="*70)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✓")
        print(f"Failed: {summary['failed']} ✗")
        print(f"Skipped: {summary['skipped']} ⊝")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        print(f"Total Duration: {summary['total_duration']:.4f}s")
        print("="*70 + "\n")
    
    def export_json(self, filename: str = "test_report.json") -> None:
        """Export report to JSON"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report exported to {filename}")


# ==================== CONFTEST FIXTURES ====================

@pytest.fixture(scope="session")
def app():
    """Create application instance for session"""
    logger.info("Setting up test application")
    return SampleApplication()


@pytest.fixture
def fresh_app():
    """Create fresh application instance for each test"""
    return SampleApplication()


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        'name': 'John Doe',
        'email': 'john@example.com'
    }


@pytest.fixture
def multiple_users():
    """Multiple user data samples"""
    return [
        {'name': 'User 1', 'email': 'user1@example.com'},
        {'name': 'User 2', 'email': 'user2@example.com'},
        {'name': 'User 3', 'email': 'user3@example.com'},
    ]


@pytest.fixture
def test_reporter():
    """Create test reporter"""
    return TestReporter()


# ==================== TEST CLASSES ====================

class TestUserCreation:
    """Test user creation functionality"""
    
    def test_add_user_success(self, fresh_app, sample_user_data):
        """Test successful user creation"""
        result = fresh_app.add_user(**sample_user_data)
        
        assert result is not None
        assert result['name'] == sample_user_data['name']
        assert result['email'] == sample_user_data['email']
        assert result['id'] > 0
    
    def test_add_user_missing_name(self, fresh_app):
        """Test user creation without name"""
        with pytest.raises(ValueError):
            fresh_app.add_user('', 'test@example.com')
    
    def test_add_user_missing_email(self, fresh_app):
        """Test user creation without email"""
        with pytest.raises(ValueError):
            fresh_app.add_user('Test User', '')
    
    def test_add_multiple_users(self, fresh_app, multiple_users):
        """Test adding multiple users"""
        for user_data in multiple_users:
            fresh_app.add_user(**user_data)
        
        assert fresh_app.get_user_count() == len(multiple_users)
    
    def test_user_id_increments(self, fresh_app, sample_user_data):
        """Test that user IDs increment correctly"""
        user1 = fresh_app.add_user(**sample_user_data)
        user2 = fresh_app.add_user(**sample_user_data)
        
        assert user2['id'] == user1['id'] + 1


class TestUserRetrieval:
    """Test user retrieval functionality"""
    
    def test_get_user_success(self, fresh_app, sample_user_data):
        """Test retrieving existing user"""
        created = fresh_app.add_user(**sample_user_data)
        retrieved = fresh_app.get_user(created['id'])
        
        assert retrieved['id'] == created['id']
        assert retrieved['name'] == created['name']
    
    def test_get_nonexistent_user(self, fresh_app):
        """Test retrieving non-existent user"""
        with pytest.raises(KeyError):
            fresh_app.get_user(9999)
    
    def test_list_users_empty(self, fresh_app):
        """Test listing users when empty"""
        users = fresh_app.list_users()
        assert len(users) == 0
    
    def test_list_users_multiple(self, fresh_app, multiple_users):
        """Test listing multiple users"""
        for user_data in multiple_users:
            fresh_app.add_user(**user_data)
        
        users = fresh_app.list_users()
        assert len(users) == len(multiple_users)


class TestUserUpdate:
    """Test user update functionality"""
    
    def test_update_user_success(self, fresh_app, sample_user_data):
        """Test successful user update"""
        user = fresh_app.add_user(**sample_user_data)
        updated = fresh_app.update_user(user['id'], name='Updated Name')
        
        assert updated['name'] == 'Updated Name'
        assert updated['email'] == sample_user_data['email']
    
    def test_update_multiple_fields(self, fresh_app, sample_user_data):
        """Test updating multiple fields"""
        user = fresh_app.add_user(**sample_user_data)
        updated = fresh_app.update_user(
            user['id'],
            name='New Name',
            email='new@example.com'
        )
        
        assert updated['name'] == 'New Name'
        assert updated['email'] == 'new@example.com'
    
    def test_update_nonexistent_user(self, fresh_app):
        """Test updating non-existent user"""
        with pytest.raises(KeyError):
            fresh_app.update_user(9999, name='Updated')


class TestUserDeletion:
    """Test user deletion functionality"""
    
    def test_delete_user_success(self, fresh_app, sample_user_data):
        """Test successful user deletion"""
        user = fresh_app.add_user(**sample_user_data)
        result = fresh_app.delete_user(user['id'])
        
        assert result is True
        with pytest.raises(KeyError):
            fresh_app.get_user(user['id'])
    
    def test_delete_nonexistent_user(self, fresh_app):
        """Test deleting non-existent user"""
        result = fresh_app.delete_user(9999)
        assert result is False
    
    def test_delete_user_reduces_count(self, fresh_app, sample_user_data):
        """Test that deletion reduces user count"""
        user = fresh_app.add_user(**sample_user_data)
        initial_count = fresh_app.get_user_count()
        
        fresh_app.delete_user(user['id'])
        new_count = fresh_app.get_user_count()
        
        assert new_count == initial_count - 1


class TestUserCount:
    """Test user count functionality"""
    
    def test_count_empty(self, fresh_app):
        """Test count on empty application"""
        assert fresh_app.get_user_count() == 0
    
    def test_count_after_add(self, fresh_app, sample_user_data):
        """Test count increases after adding user"""
        fresh_app.add_user(**sample_user_data)
        assert fresh_app.get_user_count() == 1
    
    def test_count_after_delete(self, fresh_app, sample_user_data):
        """Test count decreases after deleting user"""
        user = fresh_app.add_user(**sample_user_data)
        fresh_app.delete_user(user['id'])
        assert fresh_app.get_user_count() == 0


class TestPerformance:
    """Performance tests"""
    
    def test_add_user_performance(self, fresh_app, sample_user_data):
        """Test user addition performance"""
        result, duration = PerformanceTester.measure_execution_time(
            fresh_app.add_user,
            **sample_user_data
        )
        
        assert duration < 0.1  # Should be very fast
        assert result is not None
    
    def test_stress_test_user_creation(self, fresh_app, sample_user_data):
        """Test creating many users"""
        stats = PerformanceTester.stress_test(
            fresh_app.add_user,
            100,
            **sample_user_data
        )
        
        assert stats['iterations'] == 100
        assert fresh_app.get_user_count() == 100
        assert stats['avg_time'] < 0.01  # Average < 10ms


class TestDataValidation:
    """Data validation tests"""
    
    def test_user_has_required_fields(self, fresh_app, sample_user_data):
        """Test user has all required fields"""
        user = fresh_app.add_user(**sample_user_data)
        
        assert 'id' in user
        assert 'name' in user
        assert 'email' in user
        assert 'created_at' in user
    
    def test_user_id_is_integer(self, fresh_app, sample_user_data):
        """Test user ID is integer"""
        user = fresh_app.add_user(**sample_user_data)
        assert isinstance(user['id'], int)
    
    def test_user_name_is_string(self, fresh_app, sample_user_data):
        """Test user name is string"""
        user = fresh_app.add_user(**sample_user_data)
        assert isinstance(user['name'], str)


# ==================== PARAMETRIZED TESTS ====================

@pytest.mark.parametrize("user_data", [
    {'name': 'Alice', 'email': 'alice@example.com'},
    {'name': 'Bob', 'email': 'bob@example.com'},
    {'name': 'Charlie', 'email': 'charlie@example.com'},
])
def test_add_various_users(fresh_app, user_data):
    """Test adding various users (parametrized)"""
    user = fresh_app.add_user(**user_data)
    assert user['name'] == user_data['name']
    assert user['email'] == user_data['email']


@pytest.mark.parametrize("iterations", [10, 50, 100])
def test_create_n_users(fresh_app, sample_user_data, iterations):
    """Test creating N users (parametrized)"""
    for _ in range(iterations):
        fresh_app.add_user(**sample_user_data)
    
    assert fresh_app.get_user_count() == iterations


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
