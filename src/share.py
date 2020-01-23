from .object import MalwarecageElement, MalwarecageObject


class MalwarecageShareReason(object):
    """
    Represents the reason why object was shared with specified group
    """
    def __init__(self, api, share_data):
        self.api = api
        self._data = share_data
        self._related_object = None

    @property
    def what(self):
        """
        Returns what was shared

        :rtype: :class:`mwdblib.MalwarecageObject` or None
        """
        if self._related_object is None:
            self._related_object = MalwarecageObject.create(self.api, {
                "id": self._data["related_object_dhash"],
                "type": self._data["related_object_type"]
            })
        return self._related_object

    @property
    def why(self):
        """
        Returns why it was shared

        :return: One of actions: 'queried', 'shared', 'added', 'migrated'
        """
        return self._data["reason_type"]

    @property
    def who(self):
        """
        Returns who caused action returned by :py:attr:`why` property.

        :return: User login
        """
        return self._data["related_user_login"]

    def __str__(self):
        """
        Returns str with unparsed reason string
        """
        return "{} {}:{} by {}".format(self._data["reason_type"],
                                       self._data["related_object_type"],
                                       self._data["related_object_dhash"],
                                       self._data["related_user_login"])


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
        return MalwarecageShareReason(self.api, self.data)
