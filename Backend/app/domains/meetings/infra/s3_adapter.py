from __future__ import annotations

import asyncio
from functools import partial

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.shared.config import settings


class B2Storage:
       

    def __init__(
        self,
        *,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        bucket: str | None = None,
        region: str | None = None,
    ) -> None:
        self._bucket = (
            bucket
            or getattr(settings, "B2_BUCKET_NAME", None)
            or "decisionflow-transcripts"
        )
        endpoint = endpoint_url or getattr(settings, "B2_ENDPOINT_URL", None)
        key_id = access_key_id or getattr(settings, "B2_KEY_ID", None)
        secret = secret_access_key or getattr(settings, "B2_APPLICATION_KEY", None)
        region = region or getattr(settings, "B2_REGION", None)

        if not endpoint:
            raise RuntimeError("B2_ENDPOINT_URL is required")
        if not key_id or not secret:
            raise RuntimeError("B2 key credentials are required")
        if not region:
            raise RuntimeError("B2_REGION is required")

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    async def upload(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return key

    async def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        return await self.upload(key=key, content=data, content_type=content_type)

    async def download_bytes(self, key: str) -> bytes:
        def _get() -> bytes:
            obj = self._client.get_object(Bucket=self._bucket, Key=key)
            return obj["Body"].read()

        return await asyncio.to_thread(_get)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.head_object,
                Bucket=self._bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    async def presigned_get_url(self, key: str, expires_in: int = 3600) -> str:
        return await asyncio.to_thread(
            partial(
                self._client.generate_presigned_url,
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        )


S3Storage = B2Storage
S3Client = B2Storage