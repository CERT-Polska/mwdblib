import datetime
from typing import TYPE_CHECKING, cast

from .object import MWDBElement

if TYPE_CHECKING:
    from .api import APIClient
    from .object import MWDBElementData, MWDBObject


class MWDBComment(MWDBElement):
    """
    Represents comment for MWDB object
    """

    def __init__(
        self, api: "APIClient", data: "MWDBElementData", parent: "MWDBObject"
    ) -> None:
        super().__init__(api, data)
        self.parent = parent

    @property
    def id(self) -> int:
        """
        Comment identifier
        """
        return cast(int, self.data["id"])

    @property
    def author(self) -> str:
        """
        Comment author
        """
        return cast(str, self.data["author"])

    @property
    def timestamp(self) -> "datetime.datetime":
        """
        Comment timestamp
        """
        return datetime.datetime.fromisoformat(self.data["timestamp"])

    @property
    def comment(self) -> str:
        """
        Comment text
        """
        return cast(str, self.data["comment"])

    def delete(self) -> None:
        """
        Deletes this comment
        """
        self.api.delete("object/{}/comment/{}".format(self.parent.id, self.id))
