import click
import itertools


class ObjectFormatter(object):
    def __init__(self, humanize=True, colorize=True, pager=True):
        self.humanize = humanize
        self.colorize = colorize
        self.pager = pager

    def format_object_row(self, object):
        raise NotImplementedError()

    def format_object_list(self, objects):
        raise NotImplementedError()

    def format_file_row(self, file):
        return self.format_object_row(file)

    def format_file_detailed(self, file):
        raise NotImplementedError()

    def format_file_list(self, files):
        return self.format_object_list(files)

    def format_config_row(self, config):
        return self.format_object_row(config)

    def format_config_detailed(self, config):
        raise NotImplementedError()

    def format_config_list(self, configs):
        return self.format_object_list(configs)

    def format_blob_row(self, blob):
        return self.format_object_row(blob)

    def format_blob_detailed(self, blob):
        raise NotImplementedError()

    def format_blob_list(self, blob):
        return self.format_object_list(blob)

    def format_shares_list(self, shares):
        raise NotImplementedError()

    def format_comments_list(self, comments):
        raise NotImplementedError()

    def format_metakeys_list(self, metakeys):
        raise NotImplementedError()

    def print_lines(self, lines):
        for line in lines:
            click.echo(line.rstrip("\n"))

    def print_empty_list(self):
        return

    def print_list(self, objects, list_formatter):
        # Peek first object to check whether list is actually empty
        # This will also fetch first page and trigger error if any
        try:
            first_object = next(objects)
        except StopIteration:
            self.print_empty_list()
            return
        objects = itertools.chain([first_object], objects)
        self.print_lines(list_formatter(objects))

    def print_confirmation(self, message, **params):
        click.echo(message.format(**params))
