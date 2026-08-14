from pydantic import TypeAdapter

from app.schemas import JupyterHubUser, Paths
import httpx, os
from fastapi import FastAPI, Depends, APIRouter, Header
import uuid
from app.settings import settings
import boto3
from botocore.client import Config
import jwt

def get_seaweed_client():
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

@router.post("/create-egress")
async def create_egress(token = Depends(verify_user_token)):
    pass

@router.post("/request-egress")
async def post_files(paths: Paths, token = Depends(verify_user_token)):
    client = get_seaweed_client()
    bucket = settings.s3_bucket_name
    uploaded = []
    try:
        for path in paths.paths:
            key = os.path.basename(path)
            client.upload_file(path, bucket, key)
            uploaded.append(key)

            # Create the jwt
            project_id = uuid.uuid4()
            jwt_token = jwt.encode(
                {"projectId": "5", "userId": token.name, "bucketId": settings.s3_bucket_name},
                settings.jwt_secret_key,
                algorithm="HS256",
            )

        return {"status": "ok", "uploaded": uploaded, "token": jwt_token}
    except Exception as e:
        print(e)
        raise e

app.include_router(router)