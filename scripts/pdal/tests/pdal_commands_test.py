from scripts.pdal.pdal_commands import get_pdal_command


def test_check_pdal_command() -> None:
    """
    tests that the pdal command is built correctly
    """
    pdal_command = get_pdal_command("info", ["--option1", "value1", "--option2", "value2"])
    assert pdal_command == ["info", "--option1", "value1", "--option2", "value2"]


def test_check_pdal_command_invalid() -> None:
    """
    tests that the pdal command raises an error when an invalid command is provided
    """
    try:
        get_pdal_command("invalid_command", ["--option1", "value1"])
    except ValueError as e:
        assert str(e) == "Unsupported PDAL command: invalid_command"
    else:
        assert False, "ValueError was not raised for an invalid PDAL command"
