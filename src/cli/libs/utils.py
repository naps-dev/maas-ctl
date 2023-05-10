import base64
import contextlib
import os
import random
import socket
import string
import sys
import time

import click
import paramiko

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


def select_random_machines(n, machines):
    """
    Select n randomly selected machines from the input list.

    Args:
        n (int): Number of random machines to select.
        machines (list): A list of machines.

    Returns:
        list: A list of n randomly selected machines.
    """
    if n > len(machines):
        raise ValueError(
            f"Unable to allocate {n} machines, only {len(machines)} available"
        )

    return random.sample(machines, n)


def get_machines_by_tags(machines, tags):
    """
    Returns machines that match the tags provided.
    """
    # Create a set of tags to match against
    tag_set = {tag.lower() for tag in tags}

    # Find machines matching the tags
    matching_machines = [
        machine
        for machine in machines
        if {t.name.lower() for t in machine.tags}.intersection(tag_set)
    ]

    return matching_machines


def get_machines_by_owner(machines, name):
    """
    Returns machines that match the names provided in a case-insensitive fashion.
    """
    matching_machines = [
        machine
        for machine in machines
        if machine.owner and machine.owner.username.lower() == name.lower()
    ]

    # Check if all names were found
    if len(matching_machines) == 0:
        raise MachineNotFoundError(f"Could not find machines with owner: {name}")

    return matching_machines


def get_machines_by_pool_name(machines, names):
    """
    Returns machines that match the names provided in a case-insensitive fashion.
    """
    # Create a set of lowercased names to match against
    name_set = {name.lower() for name in names}

    # Find machines matching the names
    matching_machines = [
        machine for machine in machines if machine.pool.name.lower() in name_set
    ]

    # Check if all names were found
    found_names = {machine.pool.name.lower() for machine in matching_machines}
    if found_names != name_set:
        missing_names = name_set - found_names
        raise MachineNotFoundError(
            f"Could not find machines with names: {', '.join(missing_names)}"
        )

    return matching_machines


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


def wait_for_machine_status(machine, end_state):
    status = machine.status_message
    while status not in end_state:
        time.sleep(5)
        cur_machine = get_machine(machine.system_id)
        if status != cur_machine.status_message:
            click.echo(f"{status} {machine.hostname}...")
        status = cur_machine.status_message

    click.echo(f"{status} {machine.hostname}")


def wait_for_port(host, port, timeout=60):
    start_time = time.monotonic()
    click.echo(f"Waiting for port {port} connection...")
    while True:
        with contextlib.suppress(OSError), socket.create_connection(
            (host, port), timeout=1
        ):
            click.echo(f"Port {port} connection succeeded!")
            return True

        if time.monotonic() - start_time >= timeout:
            click.echo(f"Port {port} connection failed!")
            return False

        time.sleep(1)


def allocate_machines(machines):
    try:
        client = _get_client()
        for machine in machines:
            client.machines.allocate(hostname=machine.hostname)
    except Exception as e:
        click.echo(f"Error allocating machine {machine.hostname}: {e}")
        sys.exit(1)


def deploy_servers(machines, token, ip_addresses):
    if len(machines) < 1:
        return

    click.echo("Deploying Servers:")
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
        wait_for_machine_status(machine, ["Deployed", "Failed deployment"])
        wait_for_port(machine.ip_addresses[0], 22, 120)
        wait_for_port(machine.ip_addresses[0], 6443, 300)

    for machine in machines[1:]:
        machine.deploy(
            user_data=to_base64(secondary_cloud_init),
            distro_series="rke2-ubuntu-2204",
            hwe_kernel="generic",
        )
        wait_for_machine_status(machine, ["Deployed", "Failed deployment"])
        wait_for_port(machine.ip_addresses[0], 22, 120)
        wait_for_port(machine.ip_addresses[0], 6443, 300)


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
        wait_for_machine_status(machine, ["Deployed", "Failed deployment"])


def get_machines_ip_addresses(machines):
    """
    Gets IP addresses assigned to all network interfaces of a machine.
    This will need to change in the future but right now there is only one IP :shrug:
    """
    ips = []
    for machine in machines:
        ips.append(machine.ip_addresses[0])
    return ips


def get_ip_address(machine_name):
    """
    Gets the IP address of the machine specified by the machine-name

    Args:
        machine-name: The name of the machine to retrieve the ip address
    """
    try:
        client = _get_client()
        machines = client.machines.list()
        machine = get_machines_by_names(machines, [machine_name])[0]

        if machine.ip_addresses:
            first_ip_address = machine.ip_addresses[0]
            return f"{first_ip_address}"
        else:
            click.echo(f"No IP addresses found for {machine_name}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")


def get_kubeconfig(server, server_kubeconfig_file, local_kubeconfig_file, ssh_key=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # click.echo(os.environ.get("SSH_AUTH_SOCK"))

    if ssh_key is None:
        key = None
    elif os.path.isfile(ssh_key):
        key = paramiko.RSAKey.from_private_key_file(ssh_key)
    elif ssh_key.startswith("-----BEGIN"):
        key = paramiko.RSAKey.from_private_key(ssh_key)
    svr = f"{server}"

    ssh.connect(
        hostname=f"{svr}",
        username="ubuntu",
        allow_agent=True,
        look_for_keys=False,
        pkey=key,
    )

    sftp = ssh.open_sftp()
    sftp.get(server_kubeconfig_file, local_kubeconfig_file)
    sftp.close()

    ssh.close()
