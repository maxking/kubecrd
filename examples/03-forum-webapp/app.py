import os
import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import falcon
import kubernetes
import kubernetes_asyncio
from apischema import schema
from falcon.asgi import SSEvent
from kubecrd import OpenAPISchemaBase
from kubernetes_asyncio.client.api_client import ApiClient as AsyncApiClient


@dataclass
class Post(OpenAPISchemaBase):
    __group__ = 'forum.example.com'
    __version__ = 'v1beta1'

    id: str
    user: str
    content: str
    published: bool
    tags: list[str] = field(
        default_factory=list,
        metadata=schema(
            description='List of tags for the CRD',
            unique=False,
        ),
    )


def install_crd(resources: list[OpenAPISchemaBase]):
    """Install the list of provided resources in the Cluster."""
    kubernetes.config.load_kube_config()
    k8s_client = kubernetes.client.ApiClient()
    for resource in resources:
        resource.install(k8s_client, exist_ok=True)


class PostStreamResource:
    """Post resource represents a list of Posts."""

    async def on_get(self, req, resp):
        """Handles GET requests"""
        resp.sse = emitter(Post)


class AllPostsResource:
    """List of all posts"""

    async def on_get(self, req, resp):
        index_html = Path(__file__).parent.joinpath('index.html')
        resp.text = index_html.read_text()
        resp.content_type = 'text/html'
        resp.code = 200

    async def on_get_static(self, req, resp, filename):
        # Security, lol!
        if filename != 'sse.js':
            resp.status = 403
            resp.text = 'Request Unauthorized, Only sse.js can be accessed.'

        # Get the path to the file, if it doesn't exist, return 404.
        static = Path(__file__).parent.joinpath(filename)
        print(f'Requested static file {static=}')
        if not static.exists():
            resp.status == 404
            return

        resp.text = static.read_bytes()
        resp.content_type = 'text/javascript'
        resp.content_length = os.path.getsize(static)


async def emitter(resource):
    """emitter emits changes to the resource object as Falcon's SSE events."""
    async for happened, obj in watch_changes(resource):
        yield SSEvent(json={'happened': happened, 'object': obj.json})


async def watch_changes(resource):
    """Watch changes in resource and yield the values."""
    await kubernetes_asyncio.config.load_kube_config()
    async_client = AsyncApiClient()
    async for happened, obj in resource.async_watch(async_client):
        yield happened, obj


# Create an ASGI Falcon App that can be run using something like uvcorn.
app = falcon.asgi.App()
app.add_route('/post-sse', PostStreamResource())
app.add_route('/posts', AllPostsResource())
app.add_route('/static/{filename}', AllPostsResource(), suffix='static')


if __name__ == '__main__':
    # Run python app.py to install the CRD.
    print(f'Installing CRD {Post!r} to cluster.')
    install_crd([Post])
