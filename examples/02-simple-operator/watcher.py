import asyncio
from dataclasses import dataclass, field
from uuid import UUID

import kopf
import kubernetes
from apischema import schema

from kubecrd import schemabase

LOCK: asyncio.Lock

@dataclass
class Resource(schemabase.OpenAPISchemaBase):
    __group__ = 'example.com'
    __version__ = 'v1alpha1'

    id: str
    name: str
    tags: list[str] = field(
        default_factory=list,
        metadata=schema(
            description='regroup multiple resources',
            unique=False,
        ),
    )

@kopf.on.startup()
async def startup_fn(logger, **kwargs):
    global LOCK
    LOCK = asyncio.Lock()
    install_crd()


def install_crd():
    kubernetes.config.load_kube_config()
    k8s_client = kubernetes.client.ApiClient()
    Resource.install(k8s_client, exist_ok=True)


@kopf.on.event('resources.example.com')
async def my_handler(event, **_):
    resource = Resource.from_json(event.get('object'))
    print(f'Got resource {resource.metadata.name} in namespace {resource.metadata.namespace}')
