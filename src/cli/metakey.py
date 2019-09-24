import click

from .authenticator import pass_mwdb
from .formatters import confirm_action
from .main import main
from .types import HashFile


@main.command("metakey")
@click.argument("file-or-hash", type=HashFile())
@click.argument("key")
@click.argument("value")
@confirm_action
@pass_mwdb
def metakey_command(mwdb, file_or_hash, key, value):
    """
    Add metakey to object
    """
    obj = mwdb.query(file_or_hash)
    obj.add_metakey(key, value)
    return dict(message="Added metakey to {object_id}",
                object_id=obj.id)
