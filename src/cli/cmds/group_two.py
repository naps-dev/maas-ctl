import click

from cli.libs.click_config import pass_config


@click.group(name="images")  # type: ignore
@pass_config
def group_two(config):
    """
    Actions for managing MAAS operating system images
    """
    pass


@click.command()
@click.argument("resource-file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--name",
    required=True,
    help='Name of the image. Must be in format "os/release eg. custom/rke".',
)
@click.option(
    "--architecture",
    required=True,
    help="Architecture of the boot resource. Must be in format "
    '"arch/subarch eg. amd64/generic".',
)
@click.option("--title", required=True, help="Display name of the image in MAAS images")
@pass_config
def upload(config, resource_file, name, architecture, title):
    """
    Uploads a custom image to the MAAS server.
    """
    try:
        with open(resource_file, "rb") as f:
            config.client.boot_resources.create(
                name=name, architecture=architecture, title=title, content=f
            )

        click.echo(f"Successfully uploaded boot resource {name}")
    except Exception as e:
        click.echo(f"An error occurred: {e}")


group_two.add_command(upload)
