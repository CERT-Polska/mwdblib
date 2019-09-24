import click

from .authenticator import pass_mwdb
from .formatters import confirm_action
from .main import main
from .types import HashFile


@main.command("share")
@click.argument("file-or-hash", type=HashFile())
@click.argument("group")
@confirm_action
@pass_mwdb
def share_command(mwdb, file_or_hash, group):
    """
    Share object with another group
    """
    obj = mwdb.query(file_or_hash)
    obj.share_with(group)
    return dict(message="Shared {object_id} with {group}",
                object_id=obj.id,
                group=group)
