from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.index.index_schema import IndexOut

root_router = APIRouter(include_in_schema=False)
router = APIRouter(tags=["index"])


@root_router.get("/")
@root_router.get("/api")
def root(request: Request) -> RedirectResponse:
    return RedirectResponse(request.app.docs_url)


@router.get("", response_model=IndexOut)
def index(request: Request) -> IndexOut:
    return IndexOut(
        name=request.app.title,
        version=request.app.version,
        docs=f"{str(request.base_url).rstrip('/')}{request.app.docs_url}",
        health=str(request.url_for("health")),
    )
