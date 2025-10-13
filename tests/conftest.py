"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create test database session."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_user():
    """Create mock user for testing."""
    from database.models import User, SubscriptionType
    from datetime import datetime
    
    return User(
        id=1,
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        subscription_type=SubscriptionType.FREE,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_limits():
    """Create mock limits for testing."""
    from database.models import Limits
    
    return Limits(
        id=1,
        user_id=1,
        analytics_total=1,
        analytics_used=0,
        themes_total=1,
        themes_used=0,
        top_themes_total=0,
        top_themes_used=0
    )
