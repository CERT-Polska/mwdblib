from typing import Any, Optional, Dict
import requests

API_URL: str


class APIClient:
    api_url: str = ...
    api_key: Optional[str] = ...
    logged_user: Optional[str] = ...
    session: requests.Session = ...
    username: Optional[str] = ...
    password: Optional[str] = ...
    verify_ssl: bool = ...
    obey_ratelimiter: bool = ...
    retry_on_downtime: bool = ...
    max_downtime_retries: int = ...
    downtime_timeout: int = ...
    retry_idempotent: bool = ...
    def __init__(self, api_url: str = ..., api_key: Optional[Any] = ..., verify_ssl: bool = ..., obey_ratelimiter: bool = ..., retry_on_downtime: bool = ..., max_downtime_retries: int = ..., downtime_timeout: int = ..., retry_idempotent: bool = ...) -> None: ...
    def set_api_key(self, api_key: str) -> None: ...
    def login(self, username: str, password: str, warn: bool = ...) -> None: ...
    def logout(self) -> None: ...
    def perform_request(self, method: str, url: str, *args: Any, **kwargs: Any) -> requests.Response: ...
    def request(self, method: str, url: str, noauth: bool = ..., raw: bool = ..., *args: Any, **kwargs: Any) -> Dict[str, Any]: ...
    def get(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...
    def post(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...
    def put(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...
    def delete(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...


MalwarecageAPI = APIClient
