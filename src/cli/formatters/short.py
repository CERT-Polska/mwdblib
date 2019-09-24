import click
from .abstract import ObjectFormatter


class ShortFormatter(ObjectFormatter):
    def format_object_row(self, object):
        return object.id

    def format_file_detailed(self, object):
        return object.id

    def format_config_detailed(self, object):
        return object.id

    def format_blob_detailed(self, object):
        return object.id

    def format_object_list(self, objects):
        for object in objects:
            yield object.id

    def format_shares_list(self, shares):
        for share in shares:
            yield share.group

    def format_comments_list(self, comments):
        for comment in comments:
            yield " ".join([comment.author, comment.comment])

    def format_metakeys_list(self, metakeys):
        for key in sorted(metakeys.keys()):
            for value in metakeys[key]:
                yield " ".join([key, value])

    def print_confirmation(self, **params):
        if "object_id" in params:
            click.echo(params["object_id"])
