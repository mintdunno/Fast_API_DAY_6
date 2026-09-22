from typing import Annotated

import httpx
from fastapi import APIRouter, Depends

from fastapi_rebuild.core.http import get_http_client
from fastapi_rebuild.features.external_posts.client import JSONPlaceholderClient
from fastapi_rebuild.features.external_posts.schema import ExternalPost

router = APIRouter(
    prefix="/external-posts",
    tags=["external-posts"],
)


HttpClientDep = Annotated[
    httpx.AsyncClient,
    Depends(get_http_client),
]


def get_external_client(
    http_client: HttpClientDep,
) -> JSONPlaceholderClient:
    return JSONPlaceholderClient(http_client)


ExternalClientDep = Annotated[
    JSONPlaceholderClient,
    Depends(get_external_client),
]


@router.get(
    "/{post_id}",
    response_model=ExternalPost,
)
async def get_external_post(
    post_id: int,
    client: ExternalClientDep,
) -> ExternalPost:
    return await client.get_post(post_id)
