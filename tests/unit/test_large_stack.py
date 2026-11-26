"""Library procedures run on a large-stack thread (pywfm._dll.LargeStackLibrary)."""
import threading

import pytest

from pywfm import _dll
from pywfm.utilities import run_with_large_stack


class FakeLibrary:
    """Stands in for ctypes.CDLL: records the thread each procedure ran on."""

    def __init__(self):
        self.threads = []

    def IW_Where(self):
        self.threads.append(threading.current_thread())
        return _dll.on_large_stack()

    def IW_Fail(self):
        raise OSError("exception: stack overflow")


@pytest.fixture
def lib():
    fake = FakeLibrary()
    return fake, _dll.LargeStackLibrary(fake)


@pytest.mark.unit
def test_calls_run_on_a_large_stack_worker(lib):
    fake, wrapped = lib
    assert not _dll.on_large_stack()
    assert wrapped.IW_Where() is True
    assert fake.threads[0] is not threading.current_thread()
    assert fake.threads[0].name.startswith("pywfm-library-")


@pytest.mark.unit
def test_one_worker_per_calling_thread(lib):
    fake, wrapped = lib
    wrapped.IW_Where()
    wrapped.IW_Where()
    other = threading.Thread(target=wrapped.IW_Where)
    other.start()
    other.join()
    assert fake.threads[0] is fake.threads[1]
    assert fake.threads[2] is not fake.threads[0]


@pytest.mark.unit
def test_worker_stops_when_its_thread_ends(lib):
    fake, wrapped = lib
    other = threading.Thread(target=wrapped.IW_Where)
    other.start()
    other.join()
    fake.threads[0].join(timeout=5)
    assert not fake.threads[0].is_alive()


@pytest.mark.unit
def test_exceptions_reach_the_caller(lib):
    _, wrapped = lib
    with pytest.raises(OSError, match="stack overflow"):
        wrapped.IW_Fail()


@pytest.mark.unit
def test_missing_procedure_is_attribute_error(lib):
    _, wrapped = lib
    assert not hasattr(wrapped, "IW_Model_Switch")


@pytest.mark.unit
def test_run_with_large_stack_calls_directly(lib):
    fake, wrapped = lib
    caller = run_with_large_stack(lambda: (wrapped.IW_Where(), threading.current_thread()))
    assert caller[0] is True
    assert fake.threads[0] is caller[1]
