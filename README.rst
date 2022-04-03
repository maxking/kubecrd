========
Kube CRD
========

The primary purpose of this project is to simplify working with Kubernetes
Custom Resources. To achieve that it provides a base class,
``kubecrd.OpenAPISchemaBase`` that can create Python
dataclassses into Kubernetes Custom Resources and also generate and install
Custom Resource Definitions for those resource into the K8s cluster directly.

  >>> from dataclasses import dataclass, field
  >>> from uuid import UUID
  >>> from kubecrd import OpenAPISchemaBase
  >>> from apischema import schema

  >>> @dataclass
  ... class Resource(OpenAPISchemaBase):
  ...     __group__ = 'example.com'
  ...     __version__ = 'v1alpha1'
  ...
  ...     name: str
  ...     tags: list[str] = field(
  ...         default_factory=list,
  ...         metadata=schema(
  ...            description='regroup multiple resources',
  ...            unique=False,
  ...         ),
  ...     )

  >>> print(Resource.crd_schema())
  apiVersion: apiextensions.k8s.io/v1
  kind: CustomResourceDefinition
  metadata:
    name: resources.example.com
  spec:
    group: example.com
    names:
      kind: Resource
      plural: resources
      singular: resource
    scope: Namespaced
    versions:
    - name: v1alpha1
      schema:
        openAPIV3Schema:
          properties:
            spec:
              properties:
                name:
                  type: string
                tags:
                  default: []
                  description: regroup multiple resources
                  items:
                    type: string
                  type: array
                  uniqueItems: false
              required:
              - name
              type: object
          type: object
      served: true
      storage: true
  <BLANKLINE>


Create CRD in K8s Cluster
=========================

It is also possible to install the CRD in a cluster using a Kubernetes Client
object::

  from from kubernetes import client, config
  config.load_kube_config()
  k8s_client = client.ApiClient()
  Resource.install(k8s_client)

You can then find the resource in the cluster::

  » kubectl get crds/resources.example.com
  NAME                    CREATED AT
  resources.example.com   2022-03-20T03:58:25Z

  $ kubectl api-resources | grep example.com
  resources     example.com/v1alpha1                  true         Resource

Installation of resource is idempotent, so re-installing an already installed
resource doesn't raise any exceptions if ``exist_ok=True`` is passed in::

  Resource.install(k8s_client, exist_ok=True)


Serialization
=============

You can serialize a Resource such that it is suitable to POST to K8s::

  >>> example = Resource(name='myResource', tags=['tag1', 'tag2'])
  >>> import json
  >>> print(json.dumps(example.serialize(), sort_keys=True, indent=4))
  {
      "apiVersion": "example.com/v1alpha1",
      "kind": "Resource",
      "metadata": {
          "name": "..."
      },
      "spec": {
          "name": "myResource",
          "tags": [
              "tag1",
              "tag2"
          ]
      }
  }


Objects can also be serialized and saved directly in K8s::

  example.save(k8s_client)

Where ``client`` in the above is a Kubernetes client object. You can also use
asyncio with kubernetes_asyncio client and instead do::

  await example.async_save(k8s_async_client)


Deserialization
===============

You can deserialize the JSON from Kubernetes API into Python CR objects.
::

   $ cat -p testdata/cr.json
   {
    "apiVersion": "example.com/v1alpha1",
    "kind": "Resource",
    "metadata": {
        "generation": 1,
        "name": "myresource1",
        "namespace": "default",
        "resourceVersion": "105572812",
        "uid": "02102eb3-968b-418a-8023-75df383daa3c"
    },
    "spec": {
        "name": "bestID",
        "tags": [
            "tag1",
            "tag2"
        ]
    }
    }

by using ``from_json`` classmethod on the resource::

   >>> import json
   >>> with open('testdata/cr.json') as fd:
   ...     json_schema = json.load(fd)
   >>> res = Resource.from_json(json_schema)
   >>> print(res.name)
   bestID
   >>> print(res.tags)
   ['tag1', 'tag2']


This also loads the Kubernetes's ``V1ObjectMeta`` and sets it as the
``.metadata`` property of CR::

  >>> print(res.metadata.namespace)
  default
  >>> print(res.metadata.name)
  myresource1
  >>> print(res.metadata.resource_version)
  105572812

Watch
=====

It is possible to Watch for changes in Custom Resources using the standard
Watch API in Kubernetes. For example, to watch for all changes in Resources::


  async for happened, resource in Resource.async_watch(k8s_async_client):
      print(f'Resource {resource.metadata.name} was {happened}')


Or you can use the block sync API for the watch::


  for happened, resource in Resource.watch(k8s_client):
      print(f'Resource {resource.metadata.name} was {happened}')
  

Installing
==========

Kube CRD can be install from PyPI using pip or your favorite tool::

  $ pip install kubecrd
