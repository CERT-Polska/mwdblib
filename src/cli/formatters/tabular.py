import beautifultable
import click

from .abstract import ObjectFormatter
from .attribute import AttributeFormatter, BoldFormatter, TagFormatter, SizeFormatter, DateFormatter, \
    ObjectTypeFormatter, RelationTagFormatter

try:
    from itertools import imap
except ImportError:
    # Python 3
    imap = map


class TabularFormatter(ObjectFormatter):
    def format_attr_table(self, data):
        term_width, term_height = click.get_terminal_size()
        table = beautifultable.BeautifulTable(max_width=term_width,
                                              default_alignment=beautifultable.ALIGN_LEFT)
        table.set_style(beautifultable.STYLE_NONE)
        for key, formatter, value in data:
            key = key + ":"
            if self.colorize:
                key = click.style(key, bold=True)
            table.append_row([key, formatter.format(self, value)])
        return table.get_string()

    def format_table(self, headers, widths, row_formatter, rows):
        term_width, term_height = click.get_terminal_size()
        table = beautifultable.BeautifulTable(max_width=term_width,
                                              default_alignment=beautifultable.ALIGN_LEFT)
        table.column_headers = headers
        sum_width = None
        for width_set in widths:
            column_widths, expandable_index = width_set[:-1], width_set[-1]
            sum_width = sum(column_widths) + 6  # Table characters width
            if term_width > sum_width:
                table._column_widths = (
                        column_widths[:expandable_index] +
                        [term_width - sum_width + column_widths[expandable_index]] +
                        column_widths[expandable_index+1:]
                )
                break
        else:
            raise RuntimeError("Terminal is too narrow (needed {}, got {})".format(sum_width, term_width))
        for lines in table.stream(imap(row_formatter, rows)):
            for line in lines.splitlines():
                yield line + "\n"

    def format_object_row(self, object):
        return [
            object.id,
            ObjectTypeFormatter().format(self, object.object_type),
            TagFormatter().format(self, object.tags),
            DateFormatter().format(self, object.upload_time)
        ]

    def format_object_list(self, objects):
        return self.format_table(
            headers=["ID", "Type", "Tags", "Creation time"],
            widths=[
                [66, 12, 10, 24, 2],
                [8, 12, 10, 12, 0]
            ],
            row_formatter=self.format_object_row,
            rows=objects
        )

    def format_file_row(self, file):
        return [
            "{}\n{}".format(BoldFormatter().format(self, file.name),
                            file.sha256),
            SizeFormatter().format(self, file.size),
            "{}\n{}".format(file.type,
                            TagFormatter().format(self, file.tags)),
            DateFormatter().format(self, file.upload_time)
        ]

    def format_file_list(self, files):
        return self.format_table(
            headers=["Name/SHA256", "Size", "Type/Tags", "Creation time"],
            widths=[
                [66, 12, 10, 24, 2],
                [8, 12, 10, 12, 0]
            ],
            row_formatter=self.format_file_row,
            rows=files
        )

    def format_file_detailed(self, file):
        return self.format_attr_table([
            ["File name", AttributeFormatter(), file.name],
            ["File size", SizeFormatter(), file.size],
            ["File type", AttributeFormatter(), file.type],
            ["MD5", AttributeFormatter(), file.md5],
            ["SHA1", AttributeFormatter(), file.sha1],
            ["SHA256", AttributeFormatter(), file.sha256],
            ["SHA512", AttributeFormatter(), file.sha512],
            ["CRC32", AttributeFormatter(), file.crc32],
            ["SSDEEP", AttributeFormatter(), file.ssdeep],
            ["Upload time", DateFormatter(), file.upload_time],
            ["Tags", TagFormatter(), file.tags],
            ["Parent tags", RelationTagFormatter(), file.parents],
            ["Child tags", RelationTagFormatter(), file.children]
        ])

    def format_config_row(self, config):
        return [
            "{}\n{}".format(BoldFormatter().format(self, config.family),
                            config.id),
            config.type,
            TagFormatter().format(self, config.tags),
            DateFormatter().format(self, config.upload_time)
        ]

    def format_config_list(self, configs):
        return self.format_table(
            headers=["Family/ID", "Type", "Tags", "Creation time"],
            widths=[
                [66, 12, 10, 24, 2],
                [8, 12, 10, 12, 0]
            ],
            row_formatter=self.format_config_row,
            rows=configs
        )

    def format_config_detailed(self, config):
        import json
        attributes = [
            ["Family", AttributeFormatter(), config.family],
        ]
        for config_key in sorted(config.config_dict):
            attributes += [
                [config_key, AttributeFormatter(), json.dumps(config.config_dict[config_key])]
            ]
        attributes += [
            ["Upload time", DateFormatter(), config.upload_time],
            ["Tags", TagFormatter(), config.tags],
            ["Parent tags", RelationTagFormatter(), config.parents],
            ["Child tags", RelationTagFormatter(), config.children]
        ]
        return self.format_attr_table(attributes)

    def format_blob_row(self, blob):
        return [
            "{}\n{}".format(BoldFormatter().format(self, blob.name),
                            blob.id),
            blob.type,
            TagFormatter().format(self, blob.tags),
            DateFormatter().format(self, blob.upload_time)
        ]

    def format_blob_list(self, blobs):
        return self.format_table(
            headers=["Name/ID", "Type", "Tags", "Creation time"],
            widths=[
                [66, 12, 10, 24, 2],
                [8, 12, 10, 12, 0]
            ],
            row_formatter=self.format_blob_row,
            rows=blobs
        )

    def format_blob_detailed(self, blob):
        return self.format_attr_table([
            ["Blob name", AttributeFormatter(), blob.name],
            ["Blob size", SizeFormatter(), blob.size],
            ["Blob type", AttributeFormatter(), blob.type],
            ["SHA256", AttributeFormatter(), blob.sha256],
            ["First seen", DateFormatter(), blob.upload_time],
            ["Last seen", DateFormatter(), blob.last_seen],
            ["Tags", TagFormatter(), blob.tags],
            ["Parent tags", RelationTagFormatter(), blob.parents],
            ["Child tags", RelationTagFormatter(), blob.children]
        ])

    def format_share_row(self, share):
        return [
            BoldFormatter().format(self, share.group),
            str(share.reason),
            DateFormatter().format(self, share.timestamp)
        ]

    def format_shares_list(self, shares):
        return self.format_table(
            headers=["Group name", "Reason", "Access time"],
            widths=[
                [16, 24, 24, 1]
            ],
            row_formatter=self.format_share_row,
            rows=shares
        )

    def format_comment_row(self, comment):
        return [
            BoldFormatter().format(self, comment.author),
            comment.comment,
            DateFormatter().format(self, comment.timestamp)
        ]

    def format_comments_list(self, comments):
        return self.format_table(
            headers=["Author", "Comment", "Timestamp"],
            widths=[
                [16, 24, 24, 1]
            ],
            row_formatter=self.format_comment_row,
            rows=comments
        )

    def format_metakeys_list(self, metakeys):
        return self.format_attr_table([
            [key, AttributeFormatter(), "\n".join(value for value in metakeys[key])]
            for key in sorted(metakeys.keys())
        ])

    def print_empty_list(self):
        click.echo("No results.", err=True)

    def print_lines(self, lines):
        if self.pager:
            click.echo_via_pager(lines)
        else:
            for line in lines:
                click.echo(line.rstrip("\n"))

    def print_confirmation(self, message, **params):
        click.echo(
            message.format(
                **{k: (TagFormatter().format(self, [v]) if k == "tag" else BoldFormatter().format(self, v))
                   for k, v in params.items()}))
