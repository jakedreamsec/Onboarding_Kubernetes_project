
import pytest
from main import *


test_pods_yaml = "../test_pods.yaml"
test_namespaces_yaml = "../test_namespaces.yaml"
cluster_config_file = "~/.kube/config"
api = connect_to_cluster(cluster_config_file)


@pytest.fixture(scope="function")
def set_up_per_test():
    api.create_namespaced_pod(body=test_pods_yaml)
    pod_monitoring_loop(api)
    yield

    # Teardown
    for pod in api.list_namespaced_pod(namespace="ns1").items:
        api.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)
    for pod in api.list_namespaced_pod(namespace="ns2").items:
        api.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)
    logger.remove()

def test_pods_running():
    pass

def test_single_pod_deleted():
    pass

def test_two_pods_deleted_same_namespace():
    pass

def test_two_pods_deleted_diff_namespace():
    pass

