import json

import yaml
from apischema.json_schema import deserialization_schema
from yaml import Dumper, Loader, dump, load
from kubernetes.client.models.v1_object_meta import V1ObjectMeta


ObjectMeta_attribute_map = {
    value: key for key, value in V1ObjectMeta.attribute_map.items()
}


class OpenAPISchemaBase:
    """OpenAPISchemaBase is base class that provides methods to converts
    dataclass into an OpenAPISchema.

    """

    @classmethod
    def apischema(cls):
        """"""
        return deserialization_schema(
            cls, all_refs=False, additional_properties=True, with_schema=False
        )

    @classmethod
    def apischema_json(cls):
        return json.dumps(cls.apischema())

    @classmethod
    def apischema_yaml(cls):
        yaml_schema = load(cls.apischema_json(), Loader=Loader)
        return dump(yaml_schema, Dumper=Dumper)

    @classmethod
    def singular(cls):
        return cls.__name__.lower()

    @classmethod
    def plural(cls):
        return f'{cls.singular()}s'

    @classmethod
    def crd_schema(cls):
        crd = {
            'apiVersion': 'apiextensions.k8s.io/v1',
            'kind': 'CustomResourceDefinition',
            'metadata': {
                'name': f'{cls.plural()}.{cls.__group__}',
            },
            'spec': {
                'group': cls.__group__,
                'scope': 'Namespaced',
                'names': {
                    'singular': cls.singular(),
                    'plural': cls.plural(),
                    'kind': cls.__name__,
                },
                'versions': [
                    {
                        'name': cls.__version__,
                        # This API is served by default, currently there is no
                        # support for multiple versions.
                        'served': True,
                        'storage': True,
                        'schema': {
                            'openAPIV3Schema': {
                                'type': 'object',
                                'properties': {
                                    'spec': cls.apischema(),
                                }
                            }
                        },
                    }
                ],
            },
        }

        return dump(load(json.dumps(crd), Loader=Loader), Dumper=Dumper)

    @classmethod
    def from_json(cls, json_data):
        """Instantiate the class from json value fetched from Kubernetes.
        """
        assert json_data.get('apiVersion') == f'{cls.__group__}/{cls.__version__}'
        assert json_data.get('kind') == cls.__name__
        inputs = {}
        for key, value in json_data.get('metadata').items():
            inputs[ObjectMeta_attribute_map.get(key)] = value
        meta = V1ObjectMeta(**inputs)
        ins = cls(**json_data.get('spec'))
        ins.metadata = meta
        return ins
