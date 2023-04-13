import os

import click
import toml
from dotenv import load_dotenv
from maas.client import connect

from cli.cmds.group_one import group_one
from cli.cmds.group_two import group_two
from cli.libs.click_config import pass_config

load_dotenv()


# this is the top level command group for the cli
@click.group()  # type: ignore
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Debug output (can be used with any command group)",
)
@click.option(
    "--profile",
    default="~/.maas/credentials",
    help="Location of the MAAS credential file.",
)
@pass_config
def cli(config, verbose, profile):
    if verbose:
        config.verbose = verbose
        click.echo("Verbose mode...")

    maas_url = os.environ.get("MAAS_SERVER")
    maas_api_key = os.environ.get("MAAS_API_KEY")

    if not all([maas_url, maas_api_key]) and not os.path.exists(
        os.path.expanduser(profile)
    ):
        raise Exception(
            "MAAS_SERVER and MAAS_API_KEY environment variables are not set and maas credential file does not exist."
        )

    if all([maas_url, maas_api_key]):
        config.maas_url = maas_url
        config.maas_api_key = maas_api_key
    elif os.path.exists(os.path.expanduser(profile)):
        profile = os.path.expanduser(profile)
        try:
            with open(profile) as f:
                credentials = toml.load(f)
                config.maas_url = credentials["maas"]["url"]
                config.maas_api_key = credentials["maas"]["api_key"]
        except (FileNotFoundError, KeyError) as err:
            click.echo(err)

    config.client = connect(url=config.maas_url, apikey=config.maas_api_key)
    if config.client is None:
        click.echo("Could not load credentials from file")


cli.add_command(group_one)
cli.add_command(group_two)


if __name__ == "__main__":
    cli()
