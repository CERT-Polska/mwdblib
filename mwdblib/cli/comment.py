import click

from .formatters import confirm_action
from .main import main, pass_mwdb
from .types import HashFile


@main.command("comment")
@click.argument("file-or-hash", type=HashFile())
@click.option("--comment", prompt="Write comment")
@confirm_action
@pass_mwdb
def comment_command(mwdb, file_or_hash, comment):
    """
    Add comment to object
    """
    obj = mwdb.query(file_or_hash)
    obj.add_comment(comment)
    return dict(message="Added comment {object_id}", object_id=obj.id)
