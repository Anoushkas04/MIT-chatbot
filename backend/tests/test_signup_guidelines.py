import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.routers.auth_router as auth
from app import models
from app.moderation_engine import COMMUNITY_GUIDELINES_VERSION
from app.schemas import RegisterVerifyOTPRequest

DETAILS = {"name": "Test Student", "registration_number": "230900001", "learner_id": "test.mitmpl2023@learner.manipal.edu", "otp_code": "123456"}


@pytest.fixture
def signup(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'signup.db'}")
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    monkeypatch.setattr(auth, "SessionLocal", Session)
    monkeypatch.setattr(auth, "_validate_registration_details", lambda *a: {"admission_year": 2023, "department_name": "CSE"})
    monkeypatch.setattr(auth, "_verify_guarded", lambda *a: None)
    monkeypatch.setattr(auth, "session_response", lambda user: user.id)
    return Session


def test_signup_without_agreeing_to_guidelines_is_rejected(signup):
    with pytest.raises(HTTPException) as err:
        auth.register_verify_otp(RegisterVerifyOTPRequest(**DETAILS))
    assert err.value.status_code == 400
    assert "Community Guidelines" in err.value.detail
    assert signup().query(models.User).count() == 0


def test_signup_records_the_guidelines_version_agreed_to(signup):
    user_id = auth.register_verify_otp(RegisterVerifyOTPRequest(**DETAILS, agreed_terms=True, terms_version="2026-11"))
    user = signup().get(models.User, user_id)
    assert user.agreed_terms and user.terms_version == "2026-11" and user.terms_accepted_at is not None


def test_signup_falls_back_to_the_current_version(signup):
    user_id = auth.register_verify_otp(RegisterVerifyOTPRequest(**{**DETAILS, "learner_id": "b.mitmpl2023@learner.manipal.edu", "registration_number": "230900002"}, agreed_terms=True))
    assert signup().get(models.User, user_id).terms_version == COMMUNITY_GUIDELINES_VERSION
