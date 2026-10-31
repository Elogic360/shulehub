import uuid
import pytest
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, set_rls_tenant_context
from app.models.identity import School, User, SchoolMembership, SchoolType
from app.core.security import hash_password


@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    # Bypass RLS for test setup
    set_rls_tenant_context(session, None)
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_school(db_session: Session):
    uid = uuid.uuid4().hex[:6]
    school = School(
        name=f"Test Academy {uid}",
        code=f"SCH_{uid}".upper(),
        registration_number=f"REG/{uid}",
        school_type=SchoolType.PRIMARY,
        region="Dar es Salaam",
        district="Ilala",
        contact_email=f"school_{uid}@test.ac.tz",
        contact_phone="+255754000111",
        is_verified=True,
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


@pytest.fixture(scope="function")
def test_user(db_session: Session, test_school: School):
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"teacher_{uid}@test.ac.tz",
        phone_number=f"+255715{uid[:6]}",
        password_hash=hash_password("TestPass2026!"),
        full_name="Test Instructor",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    membership = SchoolMembership(
        school_id=test_school.id,
        user_id=user.id,
        is_active=True,
    )
    db_session.add(membership)
    db_session.commit()

    return user
