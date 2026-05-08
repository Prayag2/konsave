import pytest
from konsave.__main__ import main as konsave_main


class TestCli(object):
    """Test cases for CLI"""

    @pytest.mark.parametrize("mock_cli", ["-h"], indirect=["mock_cli"])
    def test_help(self, capsys, mock_cli, basic_kde_test_env):
        """Verify that the '-h' argument returns with exit code 0 and appropriate output."""

        with pytest.raises(SystemExit) as e:
            konsave_main()

        assert e.value.code == 0
        assert "usage: Konsave" in capsys.readouterr().out

    @pytest.mark.parametrize("mock_cli", ["-l"], indirect=["mock_cli"])
    def test_list(self, capsys, mock_cli, basic_kde_test_env):
        """
        Verify that the '-l' argument returns with exit code 0 and lists two
        profiles in output.
        """

        with pytest.raises(SystemExit) as e:
            konsave_main()

        assert e.value.code == 0
        assert "test_profile_1" and "test_profile_2" in capsys.readouterr().out


class TestCliNegative(object):
    """Negative test cases for CLI."""

    @pytest.mark.parametrize("mock_cli", ["-r does_not_exist"], indirect=["mock_cli"])
    def test_attempt_remove_non_existent_profile(
        self, capsys, mock_cli, basic_kde_test_env
    ):
        """
        Verify that the '-r' argument with non-existent profile returns with exit
        code 1 and appropriate error message in output.
        """

        with pytest.raises(SystemExit) as e:
            konsave_main()

        assert e.value.code == 1
        assert "Konsave: Profile not found." in capsys.readouterr().out

    @pytest.mark.parametrize("mock_cli", ["-i does_not_exist"], indirect=["mock_cli"])
    def test_attempt_import_non_existent_profile(
        self, capsys, mock_cli, basic_kde_test_env
    ):
        """
        Verify that the '-i' argument with non-existent profile returns with exit
        code 1 and appropriate error message in output.
        """

        with pytest.raises(SystemExit) as e:
            konsave_main()

        assert e.value.code == 1
        assert "Konsave: Not a valid konsave file" in capsys.readouterr().out
