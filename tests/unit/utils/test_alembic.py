import subprocess
from unittest.mock import MagicMock, call, patch

import pytest

from spark.utils.api import setup_alembic
from spark.utils.exceptions import AlembicError


class TestSetupAlembic:
    @patch("spark.utils.api.Path.write_text")
    @patch("spark.utils.api.env.get_template")
    @patch("spark.utils.api.subprocess.run")
    def test_setup_alembic_subprocess(
        self, mock_run, mock_get_template, mock_write_text
    ) -> None:
        output_dir = "tmp/test_project"
        setup_alembic(output_dir)

        assert mock_run.call_count == 1
        mock_run.assert_has_calls(
            [
                call(
                    ["alembic", "init", "alembic"],
                    cwd=output_dir,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ),
            ]
        )

    @patch("spark.utils.api.subprocess.run")
    @patch("spark.utils.api.env.get_template")
    @patch("spark.utils.api.Path.write_text")
    def test_setup_alembic_templates(
        self, mock_write_text, mock_get_template, mock_run
    ) -> None:
        mock_template = MagicMock()
        mock_template.render.return_value = "return content"
        mock_get_template.return_value = mock_template

        setup_alembic("tmp/test_project")

        mock_get_template.assert_called_once_with("alembic/env.py.tpl")
        mock_template.render.assert_called_once_with()
        mock_write_text.assert_called_once_with("return content")

    @patch("spark.utils.api.logger")
    @patch("spark.utils.api.subprocess.run")
    def test_setup_alembic_init_fail_raises_alembic_error(
        self, mock_run, mock_logger
    ) -> None:
        mock_run.side_effect = OSError("permission denied")

        with pytest.raises(
            AlembicError, match="Failed to initialize Alembic migrations"
        ):
            setup_alembic("tmp/test_project")

        mock_run.assert_called_once()
        mock_logger.exception.assert_called_once_with("alembic init failed")
