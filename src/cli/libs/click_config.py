import click


class Config:
    def __init__(self):
        self.verbose = False
        self.client = None
        self.maas_url = None
        self.maas_api_key = None


# this makes pass_config a singleton, so it's not reset
# when a different command group is called
pass_config = None

if pass_config is None:
    pass_config = click.make_pass_decorator(Config, ensure=True)
