import click

import cli.libs.utils as utils
from cli.libs.click_config import pass_config


@click.group(name="machines")  # type: ignore
@pass_config
def group_one(config):
    """
    Actions for interacting with MAAS machines
    """
    pass


@click.command()
@pass_config
def ls(config):
    """
    Lists all machines registered with the MAAS server.
    """
    try:
        machines = config.client.machines.list()
        for machine in machines:
            click.echo(machine.hostname)
    except Exception as e:
        click.echo(f"An error occurred: {e}")


@click.command()
@click.argument("pool-name", required=True)
@click.option("--count", default=1, help="The number of servers to allocate")
@click.option(
    "--tags",
    default=None,
    help="The tags used to select servers within the pool (ex. T1,R6515)",
)
@pass_config
def allocate_from_pool(config, pool_name, tags, count):
    """Print POOL_NAME.

    POOL_NAME is the name of the pool where servers should be allocated
    """
    machines = config.client.machines.list()

    pool_machines = utils.get_machines_by_pool_name(machines, [pool_name])

    if tags:
        pool_machines = utils.get_machines_by_tags(pool_machines, tags.split(","))

    filtered_machines = list(
        filter(
            lambda machine: machine.status_message in ["Ready", "Released"],
            pool_machines,
        )
    )

    selected_machines = utils.select_random_machines(count, filtered_machines)
    utils.allocate_machines(selected_machines)
    click.echo(",".join([machine.hostname for machine in selected_machines]))


@click.command()
@click.argument("machine-name", required=True)
@pass_config
def get_ip_address(config, machine_name):
    try:
        machines = config.client.machines.list()
        machine = utils.get_machines_by_names(machines, [machine_name])[0]

        if machine.ip_addresses:
            first_ip_address = machine.ip_addresses[0]
            click.echo(f"{first_ip_address}")
        else:
            click.echo(f"No IP addresses found for {machine_name}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")


@click.command()
@click.option(
    "--all", is_flag=True, help="Release all deployed machines without prompt."
)
@click.option(
    "--tags",
    default=None,
    help="A comma-separated list of tags to filter the deployed machines.",
)
@click.option(
    "--resource-pools", default=None, help="The names of the resource pools to release"
)
@click.option(
    "--owner", default=None, help="Owner name for which machines will be released"
)
@click.argument("machine-names", required=False)
@pass_config
def release(config, all, tags, resource_pools, owner, machine_names):
    """
    Releases specified or all machines with a "Deployed" status message.

    Args:
        machine-names: A comma separted list of machine names that should be released
    """
    try:
        machines = config.client.machines.list()
        deployed_machines = [
            machine for machine in machines if machine.status_message == "Deployed"
        ]
        if not deployed_machines:
            click.echo("No deployed machines found")
            return
        if all:
            prompt_message = (
                f"This will shutdown and release {len(machines)} machines. Are you sure you want to "
                f"continue?"
            )
            if not click.confirm(prompt_message, default=False):
                click.echo("Aborting release.")
                return
            selected_machines = machines
        elif tags:
            selected_machines = utils.get_machines_by_tags(machines, tags.split(","))
        elif resource_pools:
            selected_machines = utils.get_machines_by_pool_name(
                machines, resource_pools.split(",")
            )
        elif owner:
            selected_machines = utils.get_machines_by_owner(machines, owner)
        elif machine_names:
            selected_machines = utils.get_machines_by_names(
                machines, machine_names.split(",")
            )
        else:
            click.echo(
                "A comma separated list of machine names or the --all flag must be provided."
            )
            return
        for machine in selected_machines:
            machine.release()
            utils.wait_for_machine_status(
                machine, ["Ready", "Released", "Releasing failed"]
            )
    except Exception as e:
        click.echo(f"An error occurred: {e}")


@click.command()
@click.option(
    "--servers",
    type=str,
    default=None,
    help="Comma-separated list of server machine names",
)
@click.option(
    "--agents",
    type=str,
    default=None,
    help="Comma-separated list of agent machine names",
)
@click.option("--token", type=str, default=None, help="RKE token to use for deployment")
@pass_config
def deploy_cluster(config, servers, agents, token):
    """
    Deploys a cluster of machines with RKE2 using cloud-init.
    """
    try:
        if not any([servers, agents]):
            raise click.exceptions.UsageError(
                "At least one of --servers or --agents must be provided"
            )

        # Function to select machines
        def select_machines(server_names):
            names = server_names.split(",") if server_names else []
            count = len(names)
            if count == 0:
                return []

            # Get machines and ready machines
            all_machines = config.client.machines.list()

            machines = utils.get_machines_by_names(all_machines, names)
            current_user = config.client.users.whoami()
            ready_machines = [
                machine
                for machine in machines
                if machine.status_name in ["Ready", "Released"]
                or (
                    machine.status_name in ["Allocated"]
                    and machine.owner.username == current_user.username
                )
            ]
            if len(ready_machines) < count:
                raise utils.MachineAvailabilityError(
                    f"Not enough machines available. Need {count}, found {len(ready_machines)}."
                )
                return []
            return ready_machines

        # Select servers and agents
        selected_servers = select_machines(servers)
        selected_agents = select_machines(agents)

        # Deploy servers and agents
        token = token or utils.get_rke_token()
        all_nodes = selected_servers + selected_agents
        ip_addresses = utils.get_machines_ip_addresses(all_nodes)
        if servers:
            utils.deploy_servers(selected_servers, token, ip_addresses)
        if agents:
            utils.deploy_agents(selected_agents, token, ip_addresses)

    except utils.MachineNotFoundError:
        click.echo("One or more machines not found")
    except Exception as e:
        click.echo(f"An error occurred: {e}")


group_one.add_command(ls)
group_one.add_command(get_ip_address)
group_one.add_command(allocate_from_pool)
group_one.add_command(release)
group_one.add_command(deploy_cluster)
