import os
import sys
import pytest
import konsave.consts
import konsave.__main__


@pytest.fixture(scope="function")
def mock_cli(request, mocker):
    """Mock 'sys.argv' for testing the 'konsave' CLI interface."""

    test_args = ["konsave", request.param]

    mocker.patch.object(sys, "argv", test_args)


@pytest.fixture(scope="function")
def konsave_env_paths():
    """The 'konsave.consts' environment paths."""

    knsv_env_paths = {
        "HOME": konsave.consts.HOME,
        "CONFIG_DIR": konsave.consts.CONFIG_DIR,
        "SHARE_DIR": konsave.consts.SHARE_DIR,
        "BIN_DIR": konsave.consts.BIN_DIR,
        "KONSAVE_DIR": konsave.consts.KONSAVE_DIR,
        "PROFILES_DIR": konsave.consts.PROFILES_DIR,
        "CACHE_DIR": os.path.join(konsave.consts.HOME, ".cache"),
        "CONFIG_FILE": konsave.consts.CONFIG_FILE,
    }

    return knsv_env_paths


@pytest.fixture(scope="function")
def konsave_test_env(fs, konsave_env_paths):
    """Construct the fake filesystem directory structure for testing 'konsave'."""

    for p in [v for k, v in konsave_env_paths.items() if "FILE" not in k]:
        fs.create_dir(p)

    return fs


@pytest.fixture(scope="function")
def konsave_conf_kde(konsave_test_env):
    """Inject real 'kde' config file into the fake filesystem."""

    konsave_test_env.add_real_file(
        source_path="konsave/conf_kde.yaml",
        target_path="/home/{user_name}/.config/konsave/conf.yaml".format(
            user_name=os.getlogin()
        ),
    )

    return konsave_test_env


@pytest.fixture(scope="function")
def konsave_conf_other(konsave_test_env, konsave_env_paths):
    """Inject real 'other' config file into the fake filesystem."""

    konsave_test_env.add_real_file(
        source_path="konsave/conf_other.yaml",
        target_path=os.path.join(konsave_env_paths["CONFIG_DIR"], "conf.yaml"),
    )

    return konsave_test_env


@pytest.fixture(scope="function")
def basic_kde_test_env(mocker, konsave_conf_kde, konsave_env_paths):
    """Configure the test directory structure for a basic two profile 'konsave' environment."""

    konsave_conf_kde.create_dir(
        os.path.join(konsave_env_paths["PROFILES_DIR"], "test_profile_1")
    )
    konsave_conf_kde.create_dir(
        os.path.join(konsave_env_paths["PROFILES_DIR"], "test_profile_2")
    )

    # This must be patched because 'konsave.consts' was already loaded by this module.
    mocker.patch.object(
        konsave.__main__,
        "list_of_profiles",
        os.listdir(konsave_env_paths["PROFILES_DIR"]),
    )

    return konsave_conf_kde
