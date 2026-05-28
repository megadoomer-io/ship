import threading
import typing


class ContentCache:
    def __init__(self) -> None:
        self._generation: int = 0
        self._store: dict[str, tuple[int, object]] = {}
        self._lock = threading.Lock()

    @property
    def generation(self) -> int:
        return self._generation

    def invalidate(self) -> None:
        with self._lock:
            self._generation += 1
            self._store.clear()

    def get(self, key: str) -> object | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        gen, value = entry
        if gen != self._generation:
            return None
        return value

    def set(self, key: str, value: object) -> None:
        self._store[key] = (self._generation, value)


def cached[T](key: str, fn: typing.Callable[..., T], *args: typing.Any, **kwargs: typing.Any) -> T:
    import flask

    cache = flask.current_app.extensions.get("content_cache")
    if cache is not None:
        result = cache.get(key)
        if result is not None:
            return typing.cast(T, result)
    result = fn(*args, **kwargs)
    if cache is not None:
        cache.set(key, result)
    return result
