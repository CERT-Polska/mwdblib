import click
import functools
import os

from click_default_group import DefaultGroup

from .authenticator import pass_mwdb
from .formatters import confirm_action
from .main import main
from .types import HashFile


@main.group("upload", cls=DefaultGroup, default='file', default_if_no_args=True)
def upload_command():
    """
    Upload object into Malwarecage
    """
    pass


def upload_params(fn):
    @click.option("--parent", type=HashFile(), default=None, help="Parent file or object hash (optional)")
    @click.option("--private", is_flag=True, default=False, help="Don't share object with anyone")
    @click.option("--public", is_flag=True, default=False, help="Make object and all descendants public")
    @click.option("--share-with", default=None, help="Share object with specified group")
    @functools.wraps(fn)
    def upload_wrapped_command(*args, **kwargs):
        if sum((bool(kwargs.get("private")),
                bool(kwargs.get("public")),
                bool(kwargs.get("share_with")))) > 1:
            raise click.exceptions.UsageError("'private', 'public' and 'share-with' options are mutually exclusive")
        return fn(*args, **kwargs)
    return upload_wrapped_command


@upload_command.command("file")
@click.argument("file", type=click.Path(exists=True))
@click.option("--name", default=None, help="Original file name (default: base name from provided path)")
@upload_params
@confirm_action
@pass_mwdb
def upload_file(mwdb, file, name, parent, private, public, share_with):
    """Upload file object"""
    with click.open_file(file, 'rb') as f:
        content = f.read()
    name = name or os.path.basename(file)
    obj = mwdb.upload_file(
        name=name,
        content=content,
        parent=parent,
        private=private,
        public=public,
        share_with=share_with
    )
    return dict(message="Uploaded file {object_id}",
                object_id=obj.id)


@upload_command.command("config")
@click.argument("family")
@click.argument("config_file", type=click.Path(exists=True, allow_dash=True))
@click.option("--config-type", default="static")
@upload_params
@confirm_action
@pass_mwdb
def upload_config(mwdb, family, config_file, config_type, parent, private, public, share_with):
    """Upload config object"""
    import json
    with click.open_file(config_file, 'rb') as f:
        content = json.loads(f.read())
    obj = mwdb.upload_config(
        family=family,
        cfg=content,
        config_type=config_type,
        parent=parent,
        private=private,
        public=public,
        share_with=share_with
    )
    return dict(message="Uploaded config {object_id}",
                object_id=obj.id)


@upload_command.command("blob")
@click.argument("blob_type")
@click.argument("blob_file", type=click.Path(exists=True))
@click.option("--name", default=None, help="Original blob name (default: base name from provided path)")
@upload_params
@confirm_action
@pass_mwdb
def upload_blob(mwdb, blob_type, blob_file, name, parent, private, public, share_with):
    """Upload blob object"""
    with click.open_file(blob_file, 'rb') as f:
        content = f.read()
    name = name or os.path.basename(blob_file)
    obj = mwdb.upload_blob(
        name=name,
        type=blob_type,
        content=content,
        parent=parent,
        private=private,
        public=public,
        share_with=share_with
    )
    return dict(message="Uploaded blob {object_id}",
                object_id=obj.id)
