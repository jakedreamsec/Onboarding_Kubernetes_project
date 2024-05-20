# Todo: Import specific things, not whole library

from kubernetes import client, config
from time import sleep
from loguru import logger
import argparse
SLEEP_TIME = 2

def connect_to_cluster(cnfg_file):
    # Initial connection to cluster
    config.load_kube_config(config_file=cnfg_file)
    api = client.CoreV1Api()
    return api


def pod_monitoring_loop(api, picked_pods):

    while True:
        for pod in picked_pods:
            pod_name = pod.metadata.name
            pod_namespace = pod.metadata.namespace

            try:
                logger.info(f"Status of pod {pod_name} in namespace {pod_namespace} is: "
                            f"{api.read_namespaced_pod_status(name=pod_name,namespace=pod_namespace).status.phase}")
            except client.rest.ApiException as e:
                if "Not Found" in e.reason:
                    logger.info(f"Status of pod {pod_name} in namespace {pod_namespace} is: Deleted/Crashed")
        sleep(SLEEP_TIME)

def show_command(args, api):

    ns_list = api.list_namespace()

    if args.all_namespaces:  # No pods were specified, so show all namespaces
        ns_names = [ns.metadata.name for ns in ns_list.items]
        print("NAMESPACES:\n"+"\n".join([str(idx)+". "+name for idx, name in enumerate(ns_names, start=1)]))
        return

    if args.all_pods:
        for ns in ns_list.items:
            print("Namespace",ns.metadata.name,"contains these pods:\n"+"\n".join([str(idx)+". "+pod.metadata.name for idx, pod in enumerate(api.list_namespaced_pod(namespace=ns.metadata.name).items, start=1)]))
            # for idx, pod in enumerate(api.list_namespaced_pod(namespace=ns.metadata.name).items,start=1):
            #     print(str(idx)+".", pod.metadata.name)
        return

    # If specific namespaces were chosen:
    for ns in args.namespaces:
        print("Namespace",ns,"contains these pods:")
        for idx, pod in enumerate(api.list_namespaced_pod(namespace=ns).items,start=1):
            print(str(idx)+".", pod.metadata.name)


def monitor_command(args, api):
    if args.pods and not args.namespaces:
        print("-n/--namespaces is required when -p/--pods is specified")
        return

    picked_pods = []

    if args.all:
        picked_pods = api.list_pod_for_all_namespaces(watch=False).items

    elif args.namespaces and not args.pods:
        pod_groups = []
        for ns_name in args.namespaces:
            pod_groups.append(api.list_namespaced_pod(namespace=ns_name))
        picked_pods = [pod for pod_group in pod_groups for pod in pod_group.items]

    elif args.namespaces and args.pods:

        for ns_name in args.namespaces:
            ns_pods = api.list_namespaced_pod(ns_name)
            pod_names = [pod.metadata.name for pod in ns_pods.items]
            for pod_name in args.pods:
                if pod_name in pod_names:
                    picked_pods.append(api.read_namespaced_pod(name = pod_name,  namespace=ns_name))

    pod_monitoring_loop(api, picked_pods)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This prog is a Cluster-health-check program that logs specified pods\' health')
    subparsers = parser.add_subparsers(title="Commands", dest='command')

    parser_show_command = subparsers.add_parser('show',help="Displays the Namespaces or Pods in the cluster")
    parser_show_command.add_argument('-c','--cluster',type=str,default="~/.kube/config", help="Cluster that you choose")
    parser_show_command.add_argument('-P','--all_pods', action='store_true', help="Show all pods in all namespaces")
    parser_show_command.add_argument('-N','--all_namespaces', action='store_true', help="Show all namespaces")
    parser_show_command.add_argument('-n','--namespaces', type=str, nargs="+", help="Namespaces whose pods we want to show")
    parser_show_command.set_defaults(func=show_command)

    parser_monitor = subparsers.add_parser('monitor',help="Monitor the specified pods")
    parser_monitor.add_argument('-c','--cluster',type=str,default="~/.kube/config", nargs='*',help="Cluster to monitor")
    parser_monitor.add_argument('-n','--namespaces', type=str, nargs='*',help="The namespaces whose pods we want to monitor")
    parser_monitor.add_argument('-A','--all', action='store_true', help="Monitor all pods in all namespaces")
    parser_monitor.add_argument('-p','--pods', type=str, nargs='*', help="Specific Pods to monitor")
    parser_monitor.set_defaults(func=monitor_command)

    args = parser.parse_args()

    api = connect_to_cluster(args.cluster)

    args.func(args,api)



