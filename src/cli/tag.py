import click

from click_default_group import DefaultGroup

from .authenticator import pass_mwdb
from .formatters import confirm_action
from .main import main
from .types import HashFile


@main.group("tag", cls=DefaultGroup, default='add', default_if_no_args=True)
def tag_command():
    """
    Add/remove tags for objects
    """
    pass


@tag_command.command("add")
@click.argument("file-or-hash", type=HashFile())
@click.argument("tag")
@confirm_action
@pass_mwdb
def tag_add(mwdb, file_or_hash, tag):
    """
    Add tag
    """
    obj = mwdb.query(file_or_hash)
    obj.add_tag(tag)
    return dict(message="Added tag {tag} to {object_id}",
                tag=tag,
                object_id=obj.id)


@tag_command.command("remove")
@click.argument("file-or-hash", type=HashFile())
@click.argument("tag")
@confirm_action
@pass_mwdb
def tag_remove(mwdb, file_or_hash, tag):
    """
    Remove tag
    """
    obj = mwdb.query(file_or_hash)
    obj.remove_tag(tag)
    return dict(message="Removed tag {tag} from {object_id}",
                tag=tag,
                object_id=obj.id)
