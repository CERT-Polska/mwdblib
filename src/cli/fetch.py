import click
import os

from .authenticator import pass_mwdb
from .formatters import confirm_action
from .main import main
from .types import Hash

from ..file import MalwarecageFile


@main.command("fetch")
@click.argument("hash", type=Hash())
@click.argument("destination", type=click.Path(writable=True), required=False)
@click.option("--keep-name", is_flag=True, default=False,
              help="Store files under their original name instead of SHA256")
@confirm_action
@pass_mwdb
def fetch_command(mwdb, hash, destination, keep_name):
    """
    Download object contents
    """
    object = mwdb.query(hash)
    if destination is None:
        output_path = None
        if isinstance(object, MalwarecageFile) and keep_name:
            if object.name:
                output_path = os.path.basename(object.name)
            else:
                click.echo("Warning: Object doesn't have original name, used SHA256", err=True)
        if not output_path:
            output_path = hash
        with open(output_path, "wb") as f:
            f.write(object.content)
    else:
        output_path = destination
        with click.open_file(destination, "wb") as f:
            f.write(object.content)
    return dict(message="Downloaded {object_id} => {output_path}",
                object_id=object.id,
                output_path=output_path)
