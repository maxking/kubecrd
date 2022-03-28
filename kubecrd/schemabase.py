import json

import yaml
import kubernetes
from apischema.json_schema import deserialization_schema
from kubernetes import utils
from kubernetes.client.models.v1_object_meta import V1ObjectMeta


# ObjectMeta_attribute_map is simply the reverse of the
# V1ObjectMeta.attribute_map , which is a mapping from python attribute to json
# key while this is the opposite from json key to python attribute so that we
# can pass in the values to instantiate the V1ObjectMeta object.
ObjectMeta_attribute_map = {
    value: key for key, value in V1ObjectMeta.attribute_map.items()
}


class OpenAPISchemaBase:
    """OpenAPISchemaBase is base class that provides methods to converts dataclass
    into Kubernetes CR. It provides ability to create a Kubernetes CRD from the
    class and supports deserialization of the object JSON from K8s into Python
    obects with support for Metadata.
    """

    @classmethod
    def apischema(cls):
        """Get serialized openapi 3.0 schema for the cls.

        The output is a dict with (possibly nested) key-value pairs based on
        the schema of the class. This is used to generate the CRD schema down
        the line which rely on (a subset?) of OpenAPIV3 schema for the
        definition of a Kubernetes Custom Resource.
        """
        return deserialization_schema(
            cls, all_refs=False, additional_properties=True, with_schema=False
        )

    @classmethod
    def apischema_json(cls):
        """JSON Serialized OpenAPIV3 schema for the cls."""
        return json.dumps(cls.apischema())

    @classmethod
    def apischema_yaml(cls):
        """YAML Serialized OpenAPIV3 schema for the cls."""
        yaml_schema = yaml.load(cls.apischema_json(), Loader=yaml.Loader)
        return yaml.dump(yaml_schema, Dumper=yaml.Dumper)

    @classmethod
    def singular(cls):
        """Return the 'singular' name of the CRD.

        This is currently just the lower case name of the Python class.
        """
        return cls.__name__.lower()

    @classmethod
    def plural(cls):
        """Plural name of the CRD.

        This defaults ot just the lower case name of the Python class with an
        additional 's' in the end of the name. This might not be correct for
        all CRs though.

        TODO: Make singular and plural a configurable parameter using dunder
        attributes on cls like ``__group__`` and ``__version__``.
        """
        return f'{cls.singular()}s'

    @classmethod
    def crd_schema_dict(cls):
        """Return cls serialized as a Kubernetes CRD schema dict.

        This returns a dict representation of the Kubernetes CRD Object of cls.
        """
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
                                },
                            }
                        },
                    }
                ],
            },
        }
        return crd

    @classmethod
    def crd_schema(cls):
        """Serialized YAML representation of Kubernetes CRD definition for cls.

        This serializes the dict representation from
        :py:method:`crd_schema_dict` to YAML.
        """
        return yaml.dump(
            yaml.load(json.dumps(cls.crd_schema_dict()), Loader=yaml.Loader),
            Dumper=yaml.Dumper,
        )

    @classmethod
    def from_json(cls, json_data):
        """Instantiate the class from json value fetched from Kubernetes.

        :param json_data: The CR JSON returned from Kubernetes API.
        :type json_data: Dict
        :returns: Instantiated cls with the data from json_data.
        :rtype: cls
        """
        assert (
            json_data.get('apiVersion') == f'{cls.__group__}/{cls.__version__}'
        )
        assert json_data.get('kind') == cls.__name__
        inputs = {}
        for key, value in json_data.get('metadata').items():
            inputs[ObjectMeta_attribute_map.get(key)] = value
        meta = V1ObjectMeta(**inputs)
        ins = cls(**json_data.get('spec'))
        ins.json = json_data
        ins.metadata = meta
        return ins

    @classmethod
    def install(cls, k8s_client, exist_ok=True):
        """Install the CRD in Kubernetes.

        :param k8s_client: Instantiated Kubernetes API Client.
        :type k8s_client: kubernetes.client.api_client.ApiClient
        :param exist_ok: Boolean representing if error should be raised when
            trying to install a CRD that was already installed.
        :type exist_ok: bool
        """
        try:
            utils.create_from_yaml(
                k8s_client,
                yaml_objects=[yaml.load(cls.crd_schema(), Loader=yaml.Loader)],
            )
        except utils.FailToCreateError as e:
            code = json.loads(e.api_exceptions[0].body).get('code')
            if code == 409 and exist_ok:
                return
            raise

    @classmethod
    def watch(cls, client):
        """List and watch the changes in the Resource in Cluster."""
        api_instance = kubernetes.client.CustomObjectsApi(client)
        watch = kubernetes.watch.Watch()
        for event in watch.stream(
                func=api_instance.list_cluster_custom_object,
                group=cls.__group__,
                version=cls.__version__,
                plural=cls.plural().lower(),
                watch=True,
                allow_watch_bookmarks=True,
                timeout_seconds=50):
            obj = cls.from_json(event['object'])
            yield (event['type'], obj)

    @classmethod
    async def async_watch(cls, k8s_client):
        """Similar to watch, but uses async Kubernetes client."""
        from kubernetes_asyncio import client, watch
        api_instance = client.CustomObjectsApi(k8s_client)
        watch = watch.Watch()
        stream = watch.stream(
            func=api_instance.list_cluster_custom_object,
            group=cls.__group__,
            version=cls.__version__,
            plural=cls.plural().lower(),
            watch=True,
        )
        async for event in stream:
            obj = cls.from_json(event['object'])
            yield (event['type'], obj)
