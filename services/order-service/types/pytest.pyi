from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, overload

class MonkeyPatch:
    @overload
    def setattr(self, target: str, value: Any, raising: bool = True) -> None: ...
    @overload
    def setattr(
        self, target: Any, name: str, value: Any, raising: bool = True
    ) -> None: ...
    def setenv(self, name: str, value: str) -> None: ...

class Marker:
    def __call__(self, *args: Any, **kwargs: Any) -> Callable[..., object]: ...

class Mark:
    asyncio: Marker
    def __getattr__(self, item: str) -> Marker: ...

def fixture(
    func: Callable[..., Any] | None = None, *, autouse: bool = False
) -> Callable[..., Any]: ...
def raises(exc: type[BaseException]) -> AbstractContextManager[Any]: ...

mark: Mark
