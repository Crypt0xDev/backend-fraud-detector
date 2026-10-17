import json
import logging
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30


class StorageError(RuntimeError):
    pass


class SupabaseStorage:
    """Cliente mínimo de la API REST de Supabase Storage para un bucket privado."""

    def __init__(self, url: str, secret_key: str, bucket: str):
        self.base = f"{url.rstrip('/')}/storage/v1"
        self.secret_key = secret_key
        self.bucket = bucket

    def _request(
        self,
        method: str,
        path: str,
        body: bytes | dict | None = None,
        content_type: str = "application/json",
        headers: dict[str, str] | None = None,
    ) -> Any:
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        request = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={
                "apikey": self.secret_key,
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": content_type,
                **(headers or {}),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise StorageError(f"{method} {path}: {error.code} {detail}") from error
        except urllib.error.URLError as error:
            raise StorageError(f"{method} {path}: {error.reason}") from error
        return json.loads(payload) if payload else None

    def ensure_bucket(self) -> None:
        try:
            self._request(
                "POST",
                "/bucket",
                {"id": self.bucket, "name": self.bucket, "public": False},
            )
            logger.info("Bucket %s creado", self.bucket)
        except StorageError as error:
            if "already exists" not in str(error) and "Duplicate" not in str(error):
                raise

    def upload(self, path: str, content: bytes, content_type: str) -> None:
        self._request(
            "POST",
            f"/object/{self.bucket}/{quote(path)}",
            content,
            content_type,
            {"x-upsert": "false"},
        )

    def signed_url(self, path: str, expires_in: int, download_name: str) -> str:
        result = self._request(
            "POST",
            f"/object/sign/{self.bucket}/{quote(path)}",
            {"expiresIn": expires_in},
        )
        return f"{self.base}{result['signedURL']}&download={quote(download_name)}"

    def delete(self, paths: list[str]) -> None:
        self._request("DELETE", f"/object/{self.bucket}", {"prefixes": paths})


def open_storage(
    url: str | None, secret_key: str | None, bucket: str
) -> SupabaseStorage | None:
    if not url or not secret_key:
        logger.warning(
            "SUPABASE_URL o SUPABASE_SECRET_KEY no definidos: no se guardan lotes"
        )
        return None
    storage = SupabaseStorage(url, secret_key, bucket)
    try:
        storage.ensure_bucket()
    except StorageError:
        logger.exception("No se pudo preparar el bucket %s", bucket)
    return storage
