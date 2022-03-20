from dataclasses import dataclass, field
from uuid import UUID

from kubecrd import schemabase
from apischema import schema


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


def main():
    print(Resource.crd_schema())


if __name__ == '__main__':
    main()
