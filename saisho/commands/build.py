import datetime

import click

from ..engine import TerminalPrint, Tools, saisho_engine


@click.command("build")
@click.option("--print-only", "-p", default=False, is_flag=True)
@click.option("--compress", "-c", is_flag=True, default=False)
@click.option(
    "--output",
    "-o",
    help="Output folder",
    default=saisho_engine.OUTPUT_FOLDER,
    show_default=True,
)
@click.argument("files", nargs=-1)
def build(files: list[str] | None, print_only, compress, output):
    """
    (Re)build a file.

    Arguments:
        file -- Optional. If provided, will only build the given file.
    """
    start = datetime.datetime.now()
    opts = f"Compress [{Tools.colorize_bool(compress)}], Print Only [{Tools.colorize_bool(print_only)}]"
    TerminalPrint.header("Building Started: " + opts)
    saisho_engine._set_output_folder(output)
    # if files:
    #     saisho_engine.build_single_page(files, print_instead=print_only, compress=compress)
    # else:
    #     saisho_engine.build_all_pages(print_instead=print_only, compress=compress)
    saisho_engine.build_pages(files, print_instead=print_only, compress=compress)
    end = datetime.datetime.now()
    TerminalPrint.success(f"Finished building in {(end - start)}")
