import datetime
from typing import TYPE_CHECKING, Optional, cast

from .object import MWDBElement, MWDBObject

if TYPE_CHECKING:
    from .api import APIClient
    from .object import MWDBElementData


class MWDBShareReason:
    """
    Represents the reason why object was shared with specified group
    """

    def __init__(self, api: "APIClient", share_data: "MWDBElementData") -> None:
        self.api = api
        self._data = share_data
        self._related_object: Optional[MWDBObject] = None

    @property
    def what(self) -> MWDBObject:
        """
        Returns what was shared
        """
        if self._related_object is None:
            self._related_object = MWDBObject.create(
                self.api,
                {
                    "id": self._data["related_object_dhash"],
                    "type": self._data["related_object_type"],
                },
            )
        return self._related_object

    @property
    def why(self) -> str:
        """
        Returns why it was shared

        :return: One of actions: 'queried', 'shared', 'added', 'migrated'
        """
        return cast(str, self._data["reason_type"])

    @property
    def who(self) -> str:
        """
        Returns who caused action returned by :py:attr:`why` property.

        :return: User login
        """
        return cast(str, self._data["related_user_login"])

    def __str__(self) -> str:
        """
        Returns str with unparsed reason string
        """
        return "{} {}:{} by {}".format(
            self._data["reason_type"],
            self._data["related_object_type"],
            self._data["related_object_dhash"],
            self._data["related_user_login"],
        )


class MWDBShare(MWDBElement):
    """
    Represents share entry in MWDB object
    """

    def __init__(
        self, api: "APIClient", data: "MWDBElementData", parent: MWDBObject
    ) -> None:
        super().__init__(api, data)
        self.parent = parent

    @property
    def timestamp(self) -> "datetime.datetime":
        """
        Returns timestamp of share

        :return: datetime object with object share timestamp
        """
        return datetime.datetime.fromisoformat(self.data["access_time"])

    @property
    def group(self) -> str:
        """
        Returns a group name that object is shared with

        :return: Group name
        """
        return cast(str, self.data["group_name"])

    @property
    def reason(self) -> MWDBShareReason:
        """
        Returns why object was shared
        """
        return MWDBShareReason(self.api, self.data)
