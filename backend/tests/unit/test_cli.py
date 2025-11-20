"""Unit tests for the cli module."""

import pytest

from tarameteo.cli import (
    main,
)


def test_main_help(capsys):
    """The main function should output usage when asked for --help."""
    with pytest.raises(SystemExit):
        main(["--help"])

    captured = capsys.readouterr()
    assert "usage" in captured.out
