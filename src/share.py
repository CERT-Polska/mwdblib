import re

from .object import MalwarecageElement, MalwarecageObject


class MalwarecageShareReason(object):
    """
    Represents the reason why object was shared with specified group
    """
    def __init__(self, api, access_reason):
        self.api = api
        self._reason = access_reason
        self._data = {}
        reason_match = re.match(r"^([A-Za-z]+) [a-z_]+:([0-9A-Za-z]+) by user:([0-9A-Za-z_\-]+)$", access_reason)
        if reason_match:
            self._data = {
                "why": reason_match.group(1),
                "what": reason_match.group(2),
                "who": reason_match.group(3)
            }

    @property
    def what(self):
        """
        Returns what was shared

        :rtype: :class:`mwdblib.MalwarecageObject` or None
        """
        _what = self._data.get("what")
        if isinstance(_what, str):
            result = self.api.get("object/{}".format(_what))
            self._data["what"] = MalwarecageObject.create(self.api, result)
            return self._data["what"]
        else:
            return _what

    @property
    def why(self):
        """
        Returns why it was shared

        :return: One of actions: 'queried', 'shared', 'added'
        """
        if "why" not in self._data:
            return None
        return self._data["why"].lower()

    @property
    def who(self):
        """
        Returns who caused action returned by :py:attr:`why` property.

        :return: User login
        """
        if "who" not in self._data:
            return None
        return self._data["who"]

    def __str__(self):
        """
        Returns str with unparsed reason string (useful for custom reason entries)
        """
        return self._reason


class MalwarecageShare(MalwarecageElement):
    """
    Represents share entry in Malwarecage object
    """
    def __init__(self, api, data, parent):
        super(MalwarecageShare, self).__init__(api, data)
        self.parent = parent

    @property
    def timestamp(self):
        """
        Returns timestamp of share

        :return: datetime object with object share timestamp
        :rtype: datetime.datetime
        """
        import dateutil.parser
        return dateutil.parser.parse(self.data["access_time"])

    @property
    def group(self):
        """
        Returns a group name that object is shared with

        :return: group name
        :rtype: str
        """
        return self.data["group_name"]

    @property
    def reason(self):
        """
        Returns why object was shared

        :rtype: :class:`MalwarecageShareReason`
        """
        return MalwarecageShareReason(self.api, self.data["access_reason"])
