import click

from .authenticator import pass_mwdb
from .main import main
from .types import Hash

from ..file import MalwarecageFile


@main.command("fetch")
@click.argument("hash", type=Hash())
@click.option("--output", "-o", type=click.Path(writable=True), default=None,
              help="Store under specified path or '-' for stdout")
@click.option("--keep-name", is_flag=True, default=False,
              help="Store files under their original name instead of SHA256")
@pass_mwdb
def fetch_command(mwdb, hash, output, keep_name):
    """
    Download object contents
    """
    object = mwdb.query(hash)
    if output is None:
        if isinstance(object, MalwarecageFile) and keep_name:
            output_path = object.name
        else:
            output_path = hash
        with open(output_path, "wb") as f:
            f.write(object.content)
    else:
        output_path = output
        with click.open_file(output, "wb") as f:
            f.write(object.content)
    return dict(message="Downloaded {object_id} => {output_path}",
                object_id=object.id,
                output_path=output_path)
