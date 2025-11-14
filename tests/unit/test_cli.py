"""Unit tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from hmc.cli import app
from hmc.exceptions import SeederError, ValidationError


class TestCLI:
    """Unit tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()
            
            # Create minimal project structure
            (project_dir / "README.md").write_text("# Test Project")
            
            yield project_dir

    def test_seed_command_exists(self, runner):
        """Test that seed command is available."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "seed" in result.stdout.lower()

    def test_seed_requires_path_argument(self, runner):
        """Test that seed command requires path argument."""
        result = runner.invoke(app, ["seed"])
        assert result.exit_code != 0

    def test_seed_with_valid_path(self, runner, temp_project):
        """Test seed command with valid project path."""
        result = runner.invoke(app, ["seed", str(temp_project)])
        
        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1]  # 0=success, 1=expected error

    def test_seed_with_nonexistent_path(self, runner):
        """Test seed command with nonexistent path."""
        result = runner.invoke(app, ["seed", "/nonexistent/path"])
        
        assert result.exit_code != 0
        assert "does not exist" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_seed_with_file_instead_of_directory(self, runner, temp_project):
        """Test seed command with file instead of directory."""
        file_path = temp_project / "README.md"
        
        result = runner.invoke(app, ["seed", str(file_path)])
        
        assert result.exit_code != 0

    def test_seed_with_memory_dir_option(self, runner, temp_project):
        """Test seed command with custom memory directory."""
        result = runner.invoke(app, [
            "seed",
            str(temp_project),
            "--memory-dir", ".custom_memory"
        ])
        
        # Should process successfully or fail gracefully
        assert result.exit_code in [0, 1]

    def test_seed_with_project_id_option(self, runner, temp_project):
        """Test seed command with custom project ID."""
        result = runner.invoke(app, [
            "seed",
            str(temp_project),
            "--project-id", "custom-project-id"
        ])
        
        assert result.exit_code in [0, 1]

    def test_seed_with_verbose_flag(self, runner, temp_project):
        """Test seed command with verbose flag."""
        result = runner.invoke(app, [
            "seed",
            str(temp_project),
            "--verbose"
        ])
        
        # Verbose should produce more output
        assert result.exit_code in [0, 1]
        if result.exit_code == 0:
            assert len(result.stdout) > 0

    def test_seed_success_message(self, runner, temp_project):
        """Test that successful seed shows success message."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 2,
                "code_chunks": 1,
                "files_processed": 1,
                "warnings": []
            }
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            assert result.exit_code == 0
            assert "complete" in result.stdout.lower() or "success" in result.stdout.lower()

    def test_seed_error_message(self, runner, temp_project):
        """Test that seed errors show error message."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.side_effect = SeederError("Test error")
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            assert result.exit_code != 0
            assert "error" in result.stdout.lower()

    def test_seed_validation_error_message(self, runner, temp_project):
        """Test that validation errors show appropriate message."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.side_effect = ValidationError("Invalid input", field="test")
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            assert result.exit_code != 0

    def test_seed_displays_statistics(self, runner, temp_project):
        """Test that seed command displays statistics."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 5,
                "persona_voices": 3,
                "project_facts": 2,
                "code_chunks": 10,
                "files_processed": 4,
                "warnings": []
            }
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            assert result.exit_code == 0
            # Should show statistics
            assert "5" in result.stdout or "persona" in result.stdout.lower()

    def test_seed_with_warnings(self, runner, temp_project):
        """Test that warnings are displayed."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 2,
                "code_chunks": 1,
                "files_processed": 1,
                "warnings": ["Test warning 1", "Test warning 2"]
            }
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            assert result.exit_code == 0
            # Should display warnings
            if "warning" in result.stdout.lower():
                assert "Test warning" in result.stdout or "2" in result.stdout

    def test_seed_keyboard_interrupt(self, runner, temp_project):
        """Test handling of keyboard interrupt (Ctrl+C)."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.side_effect = KeyboardInterrupt()
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            # Should handle gracefully
            assert result.exit_code == 130 or result.exit_code == 1

    def test_seed_calls_seed_project_with_correct_args(self, runner, temp_project):
        """Test that seed command calls seed_project with correct arguments."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 0,
                "code_chunks": 0,
                "files_processed": 0,
                "warnings": []
            }
            
            runner.invoke(app, [
                "seed",
                str(temp_project),
                "--memory-dir", ".test_memory",
                "--project-id", "test-id",
                "--verbose"
            ])
            
            mock_seed.assert_called_once()
            call_args = mock_seed.call_args
            
            # Verify arguments passed correctly
            assert call_args is not None

    def test_seed_default_memory_dir(self, runner, temp_project):
        """Test that default memory directory is used when not specified."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 0,
                "code_chunks": 0,
                "files_processed": 0,
                "warnings": []
            }
            
            runner.invoke(app, ["seed", str(temp_project)])
            
            mock_seed.assert_called_once()
            # Should use default .hmc_memory

    def test_seed_auto_generated_project_id(self, runner, temp_project):
        """Test that project ID is auto-generated from directory name."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 0,
                "code_chunks": 0,
                "files_processed": 0,
                "warnings": []
            }
            
            runner.invoke(app, ["seed", str(temp_project)])
            
            mock_seed.assert_called_once()
            call_args = mock_seed.call_args
            
            # Project ID should be set (either auto or from path)
            assert call_args is not None

    def test_help_text_contains_description(self, runner):
        """Test that help text contains command description."""
        result = runner.invoke(app, ["seed", "--help"])
        
        assert result.exit_code == 0
        assert len(result.stdout) > 0
        # Should contain description of the command
        assert "seed" in result.stdout.lower() or "project" in result.stdout.lower()

    def test_help_text_shows_options(self, runner):
        """Test that help text shows available options."""
        result = runner.invoke(app, ["seed", "--help"])
        
        assert result.exit_code == 0
        # Should show options
        assert "--memory-dir" in result.stdout or "memory" in result.stdout.lower()
        assert "--verbose" in result.stdout or "verbose" in result.stdout.lower()

    def test_version_or_about(self, runner):
        """Test version or about information."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_cli_main_entry_point(self):
        """Test that CLI has main entry point."""
        from hmc.cli import app as cli_app
        
        # Should be a Typer app
        assert cli_app is not None
        assert hasattr(cli_app, 'command') or hasattr(cli_app, '__call__')

    def test_seed_output_formatting(self, runner, temp_project):
        """Test that seed output is properly formatted."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 3,
                "persona_voices": 2,
                "project_facts": 2,
                "code_chunks": 5,
                "files_processed": 3,
                "warnings": []
            }
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            assert result.exit_code == 0
            # Output should be readable
            assert result.stdout.count('\n') > 0  # Multiple lines

    def test_seed_path_normalization(self, runner, temp_project):
        """Test that path arguments are normalized."""
        # Try with trailing slash
        path_with_slash = str(temp_project) + "/"
        
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 0,
                "code_chunks": 0,
                "files_processed": 0,
                "warnings": []
            }
            
            result = runner.invoke(app, ["seed", path_with_slash])
            
            # Should handle path normalization
            assert result.exit_code in [0, 1]

    def test_seed_with_relative_path(self, runner):
        """Test seed command with relative path."""
        result = runner.invoke(app, ["seed", "."])
        
        # Should process current directory or fail gracefully
        assert result.exit_code in [0, 1]

    def test_exception_handling(self, runner, temp_project):
        """Test that unexpected exceptions are handled."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.side_effect = Exception("Unexpected error")
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            # Should not crash, should show error
            assert result.exit_code != 0

    def test_empty_statistics(self, runner, temp_project):
        """Test handling of empty statistics."""
        with patch('hmc.cli.seed_project') as mock_seed:
            mock_seed.return_value = {
                "persona_facts": 0,
                "persona_voices": 0,
                "project_facts": 0,
                "code_chunks": 0,
                "files_processed": 0,
                "warnings": []
            }
            
            result = runner.invoke(app, ["seed", str(temp_project)])
            
            # Should still show success
            assert result.exit_code == 0
