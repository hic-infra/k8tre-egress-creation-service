from email.message import EmailMessage
import hashlib
import smtplib
import ssl

from pydantic import TypeAdapter

from app.schemas import JupyterHubUser, SessionSchema
import httpx
from fastapi import FastAPI, Depends, APIRouter, File, Form, HTTPException, Header, UploadFile
from app.config import settings
import boto3
from botocore.client import Config
import jwt
from datetime import datetime

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name=settings.aws_region_name,
    )

app = FastAPI()
router = APIRouter()

async def verify_user_token(authorization: str = Header(...)):
    token = authorization.removeprefix("token ").removeprefix("Bearer ")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.jupyterhub_api_url,
            headers={"Authorization": f"token {token}"},
        )
    return TypeAdapter(JupyterHubUser).validate_json(response.content)

async def verify_session(session_id: str = Form(...)):
    """Validate and decode session JWT"""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    try:
        payload = jwt.decode(
            session_id, 
            settings.jwt_secret_key, 
            algorithms=["HS256"]
        )
        return SessionSchema(**payload)
    except jwt.DecodeError as e:
        raise HTTPException(status_code=401, detail="Invalid session token")

@router.post("/create-egress")
async def create_egress(token = Depends(verify_user_token)):
    """
    Creates a session id for a set of egress files to be uploaded
    """
    jwt_token = jwt.encode(
        {"projectId": "5", "userId": token.name, "bucketId": settings.s3_bucket_name, "time": str(datetime.now())},
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    return {"token" : jwt_token }

@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...), session_data = Depends(verify_session), token = Depends(verify_user_token)):
    """
    Uploads an invidual file to an S3 bucket for egress
    """
    try:
        contents = await file.read()
        file_hash = hashlib.sha256(contents).hexdigest()
        s3_key = f"{session_data.projectId}/{session_data.time}/{file.filename}"

        s3 = get_s3_client()
        s3.put_object(
            Key=s3_key,
            Body=contents,
            ContentType=file.content_type or "application/octet-stream",
            Bucket=settings.s3_bucket_name,
        )
        
        return {
            "uploaded": file.filename,
            "s3_key": s3_key,
        }
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Upload failed")

@router.post("/request-egress")
async def request_egress(session_id: str = Depends(verify_session), token = Depends(verify_user_token)):
    """
    Formally requests the egress check
    """
    jwt_token = jwt.encode(
        {"projectId": "5", "userId": token.name, "bucketId": settings.s3_bucket_name},
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    context = ssl.create_default_context()
    msg = EmailMessage()
    msg["to"] = settings.email_to_notify
    msg["from"] = settings.smtp_sender_email
    msg["subject"] = f"Egress Request from {token.name}"
    msg_content = f"An egress has been requested. It can be checked at {settings.egress_checking_fe_url}/{jwt_token}"
    msg.set_content(msg_content)
    with smtplib.SMTP_SSL(
        settings.smtp_server,
        settings.smtp_port,
        context=context,
        ) as server:
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)

    return {"status": "ok", "token": jwt_token}

app.include_router(router)