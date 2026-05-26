import os
import typing


class PathPrefixMiddleware:
    """WSGI middleware that strips a path prefix from incoming requests.

    Reads ``SHIP_PATH_PREFIX`` once at init.  When the prefix is non-empty and
    ``PATH_INFO`` starts with the prefix (exact match or followed by ``/``),
    the middleware moves the prefix into ``SCRIPT_NAME`` and removes it from
    ``PATH_INFO``.  Otherwise the request passes through unchanged.

    This is the standard WSGI contract used by werkzeug's
    ``DispatcherMiddleware`` and similar tools.
    """

    def __init__(self, app: typing.Callable[..., typing.Any]) -> None:
        self.app = app
        self.prefix: str = os.environ.get("SHIP_PATH_PREFIX", "")

    def __call__(
        self,
        environ: dict[str, typing.Any],
        start_response: typing.Callable[..., typing.Any],
    ) -> typing.Iterable[bytes]:
        if self.prefix:
            path_info: str = environ.get("PATH_INFO", "/")
            if path_info == self.prefix or path_info.startswith(self.prefix + "/"):
                environ["SCRIPT_NAME"] = self.prefix
                environ["PATH_INFO"] = path_info[len(self.prefix) :] or "/"

        result: typing.Iterable[bytes] = self.app(environ, start_response)
        return result
