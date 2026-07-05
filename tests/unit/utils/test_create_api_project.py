from unittest.mock import MagicMock, call, patch

from spark.utils.api import create_api_project


class TestCreateApiProject:
    @patch("spark.utils.api.env.get_template")
    @patch("spark.utils.api.Path.write_text")
    @patch("spark.utils.api.Path.mkdir")
    def test_renders_all_templates(
        self, mock_mkdir, mock_write_text, mock_get_template
    ) -> None:
        mock_template = MagicMock()
        mock_template.render.return_value = "rendered"
        mock_get_template.return_value = mock_template

        create_api_project("tmp/test_project")

        assert mock_get_template.call_count == 16
        mock_get_template.assert_has_calls(
            [
                call("README.md.tpl"),
                call("app/core/auth.py.tpl"),
                call("app/core/database.py.tpl"),
                call("app/core/exceptions.py.tpl"),
                call("app/core/logging_config.py.tpl"),
                call("app/middleware/logging_middleware.py.tpl"),
                call("app/routes/__init__.py.tpl"),
                call("app/models.py.tpl"),
                call("app/schemas.py.tpl"),
                call("app/main.py.tpl"),
                call("app/services/auth_service.py.tpl"),
                call("app/services/user_service.py.tpl"),
                call(".env.tpl"),
                call(".gitignore.tpl"),
                call(".github/workflows/ci.yaml.tpl"),
                call("process-compose.yaml.tpl"),
            ],
            any_order=True,
        )

        assert mock_template.render.call_count == 16
        for rendercall in mock_template.render.call_args_list:
            _, kwargs = rendercall
            assert "project_name" in kwargs
            assert kwargs["project_name"] == "test_project"
            assert "SECRET_KEY" in kwargs
            assert len(kwargs["SECRET_KEY"]) > 0

        assert mock_write_text.call_count == 16
        for writecall in mock_write_text.call_args_list:
            args, _ = writecall
            assert args[0] == "rendered"
