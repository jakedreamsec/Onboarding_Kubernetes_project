# Todo: Import specific things, not whole library
import argparse
from kubernetes import client, config
import sys
from time import sleep
from loguru import logger

def connect_to_cluster(cnfg_file):
    # Initial connection to cluster
    config.load_kube_config(config_file=cnfg_file)
    api = client.CoreV1Api()
    return api

# Use this func of you want to do input validation
def check_args():
    # Check that the args are valid
    pass

def check_input(user_input):
    # check that the user inputs at both stages in the program are valid
    pass

def get_namespace_input(namespace_list):
    # Gets the namespace choices from the user as indicies
    namespace_names = [ns.metadata.name for ns in namespace_list.items]
    user_input = input("\nThere are " + str(len(namespace_names)) + " namespaces to choose from." \
                                                              "\nPlease pick one or more namespaces to monitor, and pick the namespace by the given number below, separated by spaces:" \
                                                              "\n"+"\n".join([str(idx)+". "+name for idx,name in enumerate(namespace_names, start=1)]) + "\n")
    return user_input.split()

def get_pod_input(pods_list):
    # Gets the pod choices from the user as indicies
    pod_names = [pod.metadata.name for pod_group in pods_list for pod in pod_group.items]
    user_input = input("\nThere are " + str(len(pod_names)) + " pods to choose from." \
            "\nPlease pick one or more pods to monitor, and pick the pod by the given number below, separated by spaces:" \
                       "\n"+"\n".join([str(idx)+". "+name for idx,name in enumerate(pod_names, start=1)]) + "\n")
    return user_input.split()

def get_input(api):
    # The main get input function that calls the other two. After getting the namespaces, it retrieves all the pods and puts them in a new list and returns it
    ns_list = api.list_namespace()
    ns_choices = [int(i) for i in get_namespace_input(ns_list)]  # Get the namespace choices
    print(ns_choices)
    pod_list = []
    for idx in ns_choices:  # Gather all the pods from the namespaces chosen
        pod_list.append(api.list_namespaced_pod(namespace=ns_list.items[idx-1].metadata.name))

    pod_choices = [int(i) for i in get_pod_input(pod_list)]  # Get the pod choices
    flattened_pod_lst = [pod for pod_group in pod_list for pod in pod_group.items]  # flatten the 2D list to match the user's index choices
    return [flattened_pod_lst[idx-1] for idx in pod_choices]

def pod_monitoring_loop(api):
    # The loop for monitoring the chosen pods
    user_pod_picks = get_input(api) # The user chooses the pods to be monitored from the cluster namespaces
    for pod in user_pod_picks:  # Just temporarily to make sure it works
        print(pod.metadata.name)

    while True:
        for pod in user_pod_picks:
            pod_name = pod.metadata.name
            pod_namespace = pod.metadata.namespace

            try:
                logger.info(f"Status of pod {pod_name} in namespace {pod_namespace} is: {api.read_namespaced_pod_status(name=pod_name,namespace=pod_namespace).status.phase}")
            except client.rest.ApiException as e:
                if "Not Found" in e.reason:
                    logger.info(f"Status of pod {pod_name} in namespace {pod_namespace} is: Deleted")
        sleep(5)


if __name__ == "__main__":
    api = connect_to_cluster(sys.argv[1])
    pod_monitoring_loop(api)


