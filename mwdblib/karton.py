import datetime
from typing import Any, Dict, cast

from .object import MWDBElement


class MWDBKartonAnalysis(MWDBElement):
    @property
    def id(self) -> str:
        return cast(str, self.data["id"])

    @property
    def last_update(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.data["last_update"])

    @property
    def status(self) -> str:
        return cast(str, self.data["status"])

    @property
    def is_running(self) -> bool:
        return cast(str, self.data["status"]) == "running"

    @property
    def arguments(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.data["arguments"])

    @property
    def processing_in(self) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.data["processing_in"])
