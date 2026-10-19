import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import quote

from utils.token import create_download_token

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30

StorageBackend = Literal["local", "supabase"]


class StorageError(RuntimeError):
    pass


class FileStorage(Protocol):
    """Lo que se puede hacer con el almacenamiento, sea Supabase o el disco"""

    def upload(self, path: str, content: bytes, content_type: str) -> None: ...

    def signed_url(self, path: str, expires_in: int, download_name: str) -> str: ...

    def delete(self, paths: list[str]) -> None: ...


class SupabaseStorage:
    """Guarda los archivos en un bucket privado de Supabase Storage"""

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


class LocalStorage:
    """Guarda los archivos en el disco"""

    def __init__(self, root: Path, download_url: str):
        self.root = root.resolve()
        self.download_url = download_url

    def resolve(self, path: str) -> Path:
        """Ruta del archivo dentro de la carpeta; no deja salir de ella"""
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root):
            raise StorageError(f"Ruta fuera del almacenamiento: {path}")
        return target

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def upload(self, path: str, content: bytes, content_type: str) -> None:
        target = self.resolve(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as file:
                file.write(content)
        except OSError as error:
            raise StorageError(f"No se pudo guardar {path}: {error}") from error

    def signed_url(self, path: str, expires_in: int, download_name: str) -> str:
        if not self.resolve(path).is_file():
            raise StorageError(f"No existe {path}")
        token = create_download_token(path, download_name, expires_in)
        return f"{self.download_url}?token={token}"

    def delete(self, paths: list[str]) -> None:
        try:
            for path in paths:
                target = self.resolve(path)
                target.unlink(missing_ok=True)
                parent = target.parent
                if (
                    parent != self.root
                    and parent.exists()
                    and not any(parent.iterdir())
                ):
                    parent.rmdir()
        except OSError as error:
            raise StorageError(
                f"No se pudieron borrar los archivos: {error}"
            ) from error


def open_storage(
    backend: StorageBackend | None,
    *,
    local_dir: Path,
    download_url: str,
    supabase_url: str | None,
    supabase_secret_key: str | None,
    bucket: str,
) -> FileStorage | None:
    """Elige el almacenamiento según STORAGE_BACKEND"""
    if backend is None:
        backend = "supabase" if supabase_url and supabase_secret_key else None
    if backend is None:
        logger.warning("STORAGE_BACKEND no está definido: no se guardan lotes")
        return None

    if backend == "local":
        storage = LocalStorage(local_dir / bucket, download_url)
        try:
            storage.ensure_root()
        except OSError:
            logger.exception("No se pudo crear la carpeta %s", storage.root)
            return None
        logger.debug("Lotes guardados en disco local: %s", storage.root)
        return storage

    if not supabase_url or not supabase_secret_key:
        logger.warning(
            "STORAGE_BACKEND=supabase sin SUPABASE_URL o SUPABASE_SECRET_KEY: "
            "no se guardan lotes"
        )
        return None
    storage = SupabaseStorage(supabase_url, supabase_secret_key, bucket)
    try:
        storage.ensure_bucket()
    except StorageError:
        logger.exception("No se pudo preparar el bucket %s", bucket)
    logger.debug("Lotes guardados en Supabase Storage (bucket %s)", bucket)
    return storage
