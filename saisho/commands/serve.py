import click

from ..engine import saisho_engine
from ..server import Server


@click.command("serve")
@click.option(
    "--port",
    "-p",
    default=8000,
    show_default=True,
    type=int,
    help="Port to open server on",
)
@click.option(
    "--output",
    "-o",
    help="Output folder",
    default=saisho_engine.OUTPUT_FOLDER,
    show_default=True,
)
def serve(port, output):
    saisho_engine._set_output_folder(output)
    server = Server(port)
    server.run()
