import click

from .formatters import confirm_action
from .main import main, pass_mwdb
from .types import HashFile


@main.command("attribute")
@click.argument("file-or-hash", type=HashFile())
@click.argument("key")
@click.argument("value")
@confirm_action
@pass_mwdb
def attribute_command(mwdb, file_or_hash, key, value):
    """
    Add attribute to object
    """
    obj = mwdb.query(file_or_hash)
    obj.add_attribute(key, value)
    return dict(message="Added attribute to {object_id}", object_id=obj.id)
