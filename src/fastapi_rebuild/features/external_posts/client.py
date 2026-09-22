import httpx

from fastapi_rebuild.features.external_posts.schema import ExternalPost


class JSONPlaceholderClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get_post(self, post_id: int) -> ExternalPost:
        response = await self.client.get(
            f"https://jsonplaceholder.typicode.com/posts/{post_id}"
        )

        response.raise_for_status()

        return ExternalPost.model_validate(response.json())
