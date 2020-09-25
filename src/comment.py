from .object import MWDBElement


class MWDBComment(MWDBElement):
    """
    Represents comment for MWDB object
    """
    def __init__(self, api, data, parent):
        super(MWDBComment, self).__init__(api, data)
        self.parent = parent

    @property
    def id(self):
        """
        Comment identifier
        """
        return self.data["id"]

    @property
    def author(self):
        """
        Comment author

        :rtype: str
        """
        return self.data["author"]

    @property
    def timestamp(self):
        """
        Comment timestamp

        :rtype: datetime.datetime
        """
        import dateutil.parser
        return dateutil.parser.parse(self.data["timestamp"])

    @property
    def comment(self):
        """
        Comment text

        :rtype: str
        """
        return self.data["comment"]

    def delete(self):
        """
        Deletes this comment

        :raises: requests.exceptions.HTTPError
        """
        self.api.delete("object/{}/comment/{}".format(self.parent.id, self.id))


# Backwards compatibility
MalwarecageComment = MWDBComment
