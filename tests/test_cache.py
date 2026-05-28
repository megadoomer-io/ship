import threading

from ship.cache import ContentCache


class TestContentCache:
    def test_miss_returns_none(self) -> None:
        cache = ContentCache()
        assert cache.get("nonexistent") is None

    def test_set_then_get(self) -> None:
        cache = ContentCache()
        cache.set("key", [1, 2, 3])
        assert cache.get("key") == [1, 2, 3]

    def test_invalidate_clears_all(self) -> None:
        cache = ContentCache()
        cache.set("a", "value_a")
        cache.set("b", "value_b")
        cache.invalidate()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_stale_generation_returns_none(self) -> None:
        cache = ContentCache()
        cache.set("key", "old_value")
        cache.invalidate()
        assert cache.get("key") is None

    def test_invalidate_increments_generation(self) -> None:
        cache = ContentCache()
        assert cache.generation == 0
        cache.invalidate()
        assert cache.generation == 1
        cache.invalidate()
        assert cache.generation == 2

    def test_set_after_invalidate_uses_new_generation(self) -> None:
        cache = ContentCache()
        cache.set("key", "v1")
        cache.invalidate()
        cache.set("key", "v2")
        assert cache.get("key") == "v2"

    def test_concurrent_invalidate_is_safe(self) -> None:
        cache = ContentCache()
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        errors: list[Exception] = []

        def invalidate_many() -> None:
            try:
                for _ in range(50):
                    cache.invalidate()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=invalidate_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert cache.generation == 200

    def test_get_during_invalidate_returns_none_or_value(self) -> None:
        cache = ContentCache()
        cache.set("key", "value")
        results: list[object] = []

        def reader() -> None:
            for _ in range(100):
                results.append(cache.get("key"))

        def invalidator() -> None:
            for _ in range(10):
                cache.invalidate()
                cache.set("key", "new_value")

        t1 = threading.Thread(target=reader)
        t2 = threading.Thread(target=invalidator)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        for r in results:
            assert r is None or r in ("value", "new_value")
