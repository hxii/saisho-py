__NAME__ = "ＳＡＩＳＨＯ - 最 小"
__VERSION__ = "0.4"

import click

from saisho.commands.build import build
from saisho.commands.clean import clean
from saisho.commands.serve import serve
from saisho.commands.sync import sync
from saisho.commands.upload import upload

from .engine import saisho_engine


@click.group()
@click.option("--verbose", "-v", is_flag=True, default=False, envvar="VERBOSE")
@click.option("--quiet", "-q", is_flag=True, default=False, envvar="QUIET")
def cli(verbose, quiet):
    """
    ＳＡＩＳＨＯ - 最 小
    """
    click.secho(f"{__NAME__} {__VERSION__}", bold=True)
    saisho_engine.verbose = verbose
    saisho_engine.quiet = quiet
    pass


cli.add_command(build)  # Import commands from a different file
cli.add_command(sync)
cli.add_command(clean)
cli.add_command(serve)
cli.add_command(upload)

if __name__ == "__main__":
    cli()
