# maas-ctl

### Development
The project uses the following tools and patterns:
- [Python 3.10](https://www.python.org/downloads/release/python-3100/) or greater
- [Poetry](https://python-poetry.org/)
- [Click](https://click.palletsprojects.com/en/8.1.x/)
- [Flake8](https://flake8.pycqa.org/en/latest/)
- [MyPy](https://mypy-lang.org/) Not fully implemented in this project
- [Black](https://github.com/psf/black)
- [isort](https://pycqa.github.io/isort/)
- [3-Musketeers](https://3musketeers.io/)

Help is available for the supported `make` targets by running `make` in the root project directory.

```shell
make

--------------------- Run [TARGET] [ARGS] or make help for more information ---------------------

_build                         local build cli wheel file
_build_all                     local build cli
_build_image                   build cli image
_build_poetry                  build the poetry container
_dev_install                   Installs the cli locally
_dev_uninstall                 uninstalls the cli
build                          Docker build cli wheel file
build_all                      Docker build poetry image and cli image
build_image                    Docker build cli image
help                           List of targets with descriptions
push_image                     Push the image
run                            Run a docker container with the cli available
run_ci                         Run a docker container with the cli available

---------------------------------------------------------------------------------------------------
```

To install the application locally for development perform the following commands:
```shell
poetry install
poetry shell
make _dev_install
```
Create a `~/.maas/credentials` toml file with the address of the MAAS server and your api key. It should look like the following:
```toml
[maas]
url = 'http://192.168.1.10:5240/MAAS'
api_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx:yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy'
```

Or you an use environment variables:
```shell
export MAAS_SERVER=http://192.168.1.10:5240/MAAS
export MAAS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx:yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

After running the previous commands and setting your credentials you can run the `mctl` command from the shell. Any changes made to the code can be immediately tested by running `mctl [command] [subcommand]`.

for example:
```shell
mctl machines ls
```

### Project organization

The entry point to the project is `main.py` and is set in the `pyproject.toml` file.

All command groups are defined in files named for the command group in the `cmds/` directory.

Helper functions and libraries are located in the `libs/` directory.

### Adding a command
Locate the file associated with the command group you would like to add the new command to and add a function with the name of the command (use underscores instead of hypens. Click will automatically convert to hyphens for the command)


### Adding a Command Group
Add a new file for the command group in the `cmds/` directory. For example, to add a new command group called test create the file `cmds/test.py` and add the following to the file:

```python
import click
from cli.libs.click_config import pass_config


@click.group(name="test")  # type: ignore
@pass_config
def test_cmds(config):
    pass

# Add your commands
@click.command()
@click.option(...)
@pass_config
def some_new_command(config):
    pass

## add your command to the command group your created above
test.add_command(some_new_command)

```

Then in the `main.py` file add the command group to the CLI definition. It will look similar to the following:
```python
from cli.cmds.test import test_cmds
# ...
# other stuff above here

cli.add_command(more_cmds)
cli.add_command(even_moar_cmds)
```
This will allow you to start selecting and executing the new commands. They should appear in the help if you run:
```shell
$ mctl
Usage: mctl [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose               Debug output (can be used with any command
                              group)
  --help                      Show this message and exit.

Commands:
  group-one
  group-two
  some-new-command
```

# Uninstallation

[(Back to top)](#table-of-contents)

### Locally

1. Uninstall the required packages.
   ```shell
   make _dev_uninstall
   ```
