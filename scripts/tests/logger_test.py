import json

from logger import LOGGER
from pytest import CaptureFixture


def test_logger(capsys: CaptureFixture[str]) -> None:
    LOGGER.debug("test_get_logger")
    stdout, _ = capsys.readouterr()
    log = json.loads(stdout)

    assert log["msg"] == "test_get_logger"
    assert log["hostname"]
