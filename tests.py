

import pytest
from main import connect_to_cluster, pod_monitoring_loop, show_command, monitor_command
from unittest.mock import patch, Mock




test_pods_yaml = "../test_pods.yaml"
test_namespaces_yaml = "../test_namespaces.yaml"
cluster_config_file = "~/.kube/config"
api = connect_to_cluster(cluster_config_file)
test_namespace_pod_dict = {"ns1":["pod1","pod2"],"ns2":["pod3","pod4"]}


class Fake_Args:
    def __init__(self):

        self.cluster = []
        self._namespaces = []
        self._pods = []
        self.all_namespaces = False
        self.all_pods = False
        self.all = False
        
        
    # Replacement Methods
    def cluster(self):
        pass
    def namespaces(self):
        return self._namespaces
    def pods(self):
        return self._pods


    # Utility methods
    def set_all_namespaces(self,val):
        self.all_namespaces = val
    def set_all_pods(self,val):
        self.all_pods = val
    def insert_pods(self,*pods):
        for pod in pods:
            self._pods.append(pod)
    def insert_namespaces(self,*namespaces):
        for ns in namespaces:
            self._namespaces.append(ns)





@pytest.fixture
def test_args():
    _test_args = Fake_Args()
    _test_args.insert_pods(*test_namespace_pod_dict.keys())
    _test_args.insert_namespaces(*[pod for ns in test_namespace_pod_dict.values() for pod in ns])
    yield _test_args

def list_namespaced_pod_side_effect(ns,fake_pod_lists):
    mock_response = Mock(name="lnp_response")
    if ns == "ns1":
        mock_response.items = fake_pod_lists[0]
    if ns == "ns2":
        mock_response.items = fake_pod_lists[1]
    return mock_response

def read_namespaced_pod_status(pod, ns):
    mock_response = Mock(name="rnps_response")
    mock_response.status.phase = "Running"

@pytest.fixture
def mock_objects():
    with (patch('main.client.CoreV1Api') as mock_k8s_api, patch('main.config.load_kube_config') as mock_k8s_config, patch('main.print') as mock_print,
          patch('main.logger') as mock_logger):


        fake_ns_lst = []
        fake_pod_group = [] # A list of fake pods
        fake_pods_lsts = [] # A list of lists of fake pods
        for ns in test_namespace_pod_dict:
            new_mock_ns = Mock(name=ns)
            new_mock_ns.metadata.name = ns
            fake_ns_lst.append(new_mock_ns)

            for pod in test_namespace_pod_dict[ns]:
                new_mock_pod = Mock(name=pod)
                new_mock_pod.metadata.name = pod
                new_mock_pod.metadata.namespace = ns
                new_mock_pod.metadata.status.phase = "Running"
                fake_pod_group.append(new_mock_pod)

            fake_pods_lsts.append(fake_pod_group)
            fake_pod_group = []


        mock_k8s_api.read_namespaced_pod_status(name=pod, namespace=ns).status.phase.return_value = "Running"

        mock_k8s_api.list_namespaced_pod(namespace=ns).items = fake_pod_lst

        mock_ns_list = Mock()
        mock_k8s_api.list_namespace.return_value = mock_ns_list
        mock_ns_list.items = fake_ns_lst



        yield {"api":mock_k8s_api, "print":mock_print,"config":mock_k8s_config,"logger":mock_logger}


def test_show_all_namespaces(test_args, mock_objects):

    test_args.set_all_namespaces(True)
    show_command(test_args, mock_objects["api"])
    ns_names = [ns_name for ns_name in test_namespace_pod_dict]
    mock_objects["print"].assert_called_once_with("NAMESPACES:\n" + "\n".join([str(idx) + ". " + name for idx, name in enumerate(ns_names, start=1)]))
    mock_objects["print"].assert_called_once()

def test_show_all_pods(test_args, mock_objects):

    test_args.set_all_pods(True)
    show_command(test_args, mock_objects["api"])

    ns_names = [ns_name for ns_name in test_namespace_pod_dict]
    for ns in ns_names:
        pod_names = [pod for pod in test_namespace_pod_dict[ns]]
        mock_objects["print"].assert_any_call("Namespace", ns, "contains these pods:\n" + "\n".join([str(idx) + ". " + name for idx, name in enumerate(pod_names, start=1)]))




def test_single_pod_deleted(caplog):
    pass


def test_two_pods_deleted_same_namespace(caplog):
    pass


def test_two_pods_deleted_diff_namespace(caplog):
    pass

