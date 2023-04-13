import base64
import random
import string
import time

import click
from yaspin import yaspin

from cli.libs.click_config import pass_config


@pass_config
def _get_client(config):
    return config.client


class MachineNotFoundError(Exception):
    """
    Exception raised when a machine is not found.
    """

    pass


class MachineAvailabilityError(Exception):
    """
    Exception raised when a machine is not found.
    """

    pass


def get_machines_by_names(machines, names):
    """
    Returns machines that match the names provided in a case-insensitive fashion.
    """
    # Create a set of lowercased names to match against
    name_set = {name.lower() for name in names}

    # Find machines matching the names
    matching_machines = [
        machine for machine in machines if machine.hostname.lower() in name_set
    ]

    # Check if all names were found
    found_names = {machine.hostname.lower() for machine in matching_machines}
    if found_names != name_set:
        missing_names = name_set - found_names
        raise MachineNotFoundError(
            f"Could not find machines with names: {', '.join(missing_names)}"
        )

    return matching_machines


def get_machine(system_id):
    client = _get_client()
    machines = client.machines.list()

    filtered_machines = list(
        filter(lambda machine: machine.system_id == system_id, machines)
    )

    if len(filtered_machines) == 0:
        raise ValueError(f"No machine found with system ID '{system_id}'")
    elif len(filtered_machines) > 1:
        raise ValueError(f"Multiple machines found with system ID '{system_id}'")
    else:
        machine = filtered_machines[0]

    return machine


def to_base64(input_str):
    input_bytes = input_str.encode("ascii")
    encoded_bytes = base64.b64encode(input_bytes)
    encoded_str = encoded_bytes.decode("ascii")
    return encoded_str


def get_rke_token():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


def get_server_cloud_init(token, ip_addresses):
    # - '\curl -sfL https://get.rke2.io | INSTALL_RKE2_VERSION=$RKE2_VERSION sh -'
    primary_server_cloud_init = f"""
#cloud-config
write_files:
  - path: /etc/rancher/rke2/config.yaml
    owner: root:root
    permissions: 0600
    defer: true
    content: |
      bind-address: {ip_addresses[0]}
      token: {token}
      disable-cloud-controller: true
      write-kubeconfig-mode: 644
      disable:
        - "rke2-ingress-nginx"

runcmd:
 - 'sudo bash -c "/opt/setup.sh server | tee /tmp/setup.log"'
"""

    secondary_server_cloud_init = f"""
#cloud-config
write_files:
  - path: /etc/rancher/rke2/config.yaml
    owner: root:root
    permissions: 0600
    defer: true
    content: |
      server: https://{ip_addresses[0]}:9345
      token: {token}
      disable-cloud-controller: true
      write-kubeconfig-mode: 644
      disable:
        - "rke2-ingress-nginx"

runcmd:
 - 'sudo bash -c "/opt/setup.sh server | tee /tmp/setup.log"'
"""
    return primary_server_cloud_init, secondary_server_cloud_init


def get_agent_cloud_init(token, ip_addresses):
    # - '\curl -sfL https://get.rke2.io | INSTALL_RKE2_VERSION=$RKE2_VERSION sh -'
    agent_cloud_init = f"""
#cloud-config
write_files:
  - path: /etc/rancher/rke2/config.yaml
    owner: root:root
    permissions: 0600
    defer: true
    content: |
      server: https://{ip_addresses[0]}:9345
      token: {token}
      write-kubeconfig-mode: 644

runcmd:
 - 'sudo bash -c "/opt/setup.sh agent | tee /tmp/setup.log"'
"""
    return agent_cloud_init


def wait_for_deployment(machine):
    system_id = machine.system_id
    status = machine.status_message
    hostname = machine.hostname
    with yaspin(text=f"{status} {hostname} ", color="yellow") as spinner:
        while status not in ["Deployed", "Failed deployment"]:
            time.sleep(5)  # time consuming code
            cur_machine = get_machine(system_id)
            status = cur_machine.status_message

        if status == "Deployed":
            spinner.ok("✅")
        else:
            spinner.fail("💥")


def allocate_machines(machines):
    client = _get_client()
    for machine in machines:
        client.machines.allocate(hostname=machine.hostname)


def deploy_servers(machines, token, ip_addresses):
    if len(machines) < 1:
        return

    click.echo("Deploying Servers...")
    primary_cloud_init, secondary_cloud_init = get_server_cloud_init(
        token, ip_addresses
    )
    # print(server_cloud_init)
    for machine in machines[:1]:
        machine.deploy(
            user_data=to_base64(primary_cloud_init),
            distro_series="rke2-ubuntu-2204",
            hwe_kernel="generic",
        )
        wait_for_deployment(machine)

    for machine in machines[1:]:
        machine.deploy(
            user_data=to_base64(secondary_cloud_init),
            distro_series="rke2-ubuntu-2204",
            hwe_kernel="generic",
        )
        wait_for_deployment(machine)


def deploy_agents(machines, token, ip_addresses):
    if len(machines) < 1:
        return

    click.echo("Deploying Agents...")
    agent_cloud_init = get_agent_cloud_init(token, ip_addresses)
    # print(agent_cloud_init)
    for machine in machines:
        machine.deploy(
            user_data=to_base64(agent_cloud_init),
            distro_series="rke2-ubuntu-2204",
            hwe_kernel="generic",
        )
        wait_for_deployment(machine)


def get_machines_ip_addresses(machines):
    """
    Gets IP addresses assigned to all network interfaces of a machine.
    This will need to change in the future but right now there is only one IP :shrug:
    """
    ips = []
    for machine in machines:
        ips.append(machine.ip_addresses[0])
    return ips
