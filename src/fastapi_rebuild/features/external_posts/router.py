from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from fastapi_rebuild.core.http import get_http_client

router = APIRouter(
    prefix="/external-posts",
    tags=["external-posts"],
)

HttpClientDep = Annotated[
    httpx.AsyncClient,
    Depends(get_http_client),
]


@router.get("/{post_id}")
async def get_external_post(
    post_id: int,
    client: HttpClientDep,
):
    response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")

    return response.json()
