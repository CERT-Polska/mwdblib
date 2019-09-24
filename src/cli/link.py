import click

from .authenticator import pass_mwdb
from .formatters import confirm_action
from .main import main
from .types import HashFile


@main.command("link")
@click.argument("parent", type=HashFile())
@click.argument("child", type=HashFile())
@confirm_action
@pass_mwdb
def link_command(mwdb, parent, child):
    """
    Set relationship for objects
    """
    parent_obj = mwdb.query(parent)
    child_obj = mwdb.query(child)
    parent_obj.add_child(child_obj)
    return dict(message="Added relationship {parent} => {child}",
                parent=parent_obj.id,
                child=child_obj.id)
