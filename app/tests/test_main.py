from io import BytesIO

import boto3
from fastapi.testclient import TestClient
import jwt
from moto import mock_aws
from pydantic import TypeAdapter
import pytest
from app.main import app, verify_user_token
from app.config import settings
from datetime import datetime

from app.schemas import JupyterHubUser
client = TestClient(app)

example_user = {
    "kind": "user",
    "last_activity": "2026-08-14 10:30:45",
    "groups": ["researchers", "project-001", "data-access"],
    "name": "researcher_001",
    "admin": False,
    "token_id": "abc123def456",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "scopes": ["read:notebooks", "access:servers", "read:groups"]
}

@pytest.fixture
def authed_client():
    app.dependency_overrides[verify_user_token] = lambda: JupyterHubUser(**example_user)
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def s3_mock():
    """Mock S3"""
    with mock_aws():
        # Create bucket
        s3 = boto3.client('s3', region_name='eu-west-2')
        s3.create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
        )
        yield s3

def test_create_session(authed_client):
    """Test session creation"""
    response = authed_client.post(
        "/create-egress",
        headers={"Authorization": "Bearer example"}
        )
    assert response.status_code == 200
    res = response.json()
    data = jwt.decode(res["token"], settings.jwt_secret_key, algorithms=["HS256"])

def test_upload_invalid_session(authed_client):
    """Test upload with invalid session"""
    response = authed_client.post(
        "/upload-file",
        data={"session_id": "invalid-session-id"},
        files={"file": ("test.csv", BytesIO(b"data"), "text/csv")}
    )
    
    assert response.status_code == 401
    assert "Invalid session token" in response.json()['detail']


def test_upload_no_session(authed_client):
    """Test upload without session_id"""
    response = authed_client.post(
        "/upload-file",
        files={"file": ("test.csv", BytesIO(b"data"), "text/csv")}
    )
    
    assert response.status_code == 422

def test_successful_upload(authed_client):
    response = authed_client.post(
        "/create-egress",
        )
    assert response.status_code == 200
    res = response.json()
    session_id = res["token"]
    response = authed_client.post(
        "/upload-file",
        data={"session_id": session_id},
        files={"file": ("test.csv", BytesIO(b"data"), "text/csv")}
    )

    assert response.status_code == 200

def test_successful_egress_request(authed_client):
    response = authed_client.post(
        "/create-egress",
        )
    assert response.status_code == 200
    res = response.json()
    session_id = res["token"]
    response = authed_client.post(
        "/upload-file",
        data={"session_id": session_id},
        files={"file": ("test.csv", BytesIO(b"data"), "text/csv")}
    )

    assert response.status_code == 200

    response = authed_client.post(
        "/request-egress",
        data={"session_id": session_id},
        files={"file": ("test.csv", BytesIO(b"data"), "text/csv")}
    )

    assert response.status_code == 200