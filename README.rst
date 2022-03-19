========
Kube CRD
========

The primary purpose of this project is to simplify working with Kubernetes
Custom Resources. To achieve that it provides a base class,
:py:class:`kubecrd.OpenAPISchemaBase` that can convert regular Python
dataclassses into Kubernetes Custom Resource Definitions.


  >>> from dataclasses import dataclass, field
  >>> from uuid import UUID
  >>> from kubecrd import OpenAPISchemaBase
  >>> from apischema import schema

  >>> @dataclass
  ... class Resource(OpenAPISchemaBase):
  ...     __group__ = 'example.com'
  ...     __version__ = 'v1alpha1'
  ...
  ...     id: UUID
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
            id:
              format: uuid
              type: string
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
          - id
          - name
          type: object
      served: true
      storage: true
  <BLANKLINE>
