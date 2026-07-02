import subprocess
from unittest.mock import call, patch

import pytest

from spark.utils.api import initialize_dependencies
from spark.utils.deps import API_DEPS
from spark.utils.exceptions import DependencyError


class TestInitializeDependencies:
    @patch("spark.utils.api.subprocess.run")
    @patch("spark.utils.api.Path.unlink")
    def test_happy_path_dependency_installation(self, mock_unlink, mock_run) -> None:
        output_dir = "tmp/test_project"

        initialize_dependencies(output_dir)

        assert mock_run.call_count == 2
        mock_run.assert_has_calls(
            [
                call(
                    ["uv", "init", "--no-readme"],
                    cwd=output_dir,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
                call(
                    ["uv", "add", *API_DEPS],
                    cwd=output_dir,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
            ]
        )
        mock_unlink.assert_called_once_with(missing_ok=True)

    @patch("spark.utils.api.logger")
    @patch("spark.utils.api.subprocess.run")
    @patch("spark.utils.api.Path.unlink")
    def test_uv_init_fails_raises_dependency_error(
        self, mock_unlink, mock_run, mock_logger
    ) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["uv", "init", "--no-readme"]
        )

        with pytest.raises(
            DependencyError, match="Failed to install project dependencies"
        ):
            initialize_dependencies("tmp/test_project")

        mock_run.assert_called_once()
        mock_unlink.assert_not_called()
        mock_logger.exception.assert_called_once_with("dependency installation failed")

    @patch("spark.utils.api.logger")
    @patch("spark.utils.api.subprocess.run")
    @patch("spark.utils.api.Path.unlink")
    def test_uv_add_fails_raises_dependency_error(
        self, mock_unlink, mock_run, mock_logger
    ) -> None:
        mock_run.side_effect = [
            None,
            subprocess.CalledProcessError(1, ["uv", "add", *API_DEPS]),
        ]

        with pytest.raises(
            DependencyError, match="Failed to install project dependencies"
        ):
            initialize_dependencies("tmp/test_project")

        assert mock_run.call_count == 2
        mock_unlink.assert_called_once_with(missing_ok=True)
        mock_logger.exception.assert_called_once_with("dependency installation failed")

    @patch("spark.utils.api.logger")
    @patch("spark.utils.api.subprocess.run")
    @patch("spark.utils.api.Path.unlink")
    def test_oserror_raises_dependency_error(
        self, mock_unlink, mock_run, mock_logger
    ) -> None:
        mock_run.side_effect = OSError("permission denied")

        with pytest.raises(
            DependencyError, match="Failed to install project dependencies"
        ):
            initialize_dependencies("tmp/test_project")

        mock_run.assert_called_once()
        mock_unlink.assert_not_called()
        mock_logger.exception.assert_called_once_with("dependency installation failed")
