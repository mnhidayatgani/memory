"""CLI interface for HMC using Typer.

Provides the `hmc seed` command for seeding projects.
"""

from pathlib import Path

import typer

from hmc.exceptions import SeederError
from hmc.seeder import seed_project

app = typer.Typer(help="Hybrid Memory Core (HMC) - Persistent memory for AI agents")


@app.command()
def seed(
    path: Path = typer.Argument(
        ...,
        help="Path to project directory to seed",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    memory_dir: Path = typer.Option(
        ".hmc_memory",
        "--memory-dir",
        "-m",
        help="Memory storage directory (relative to project path)",
    ),
    project_id: str | None = typer.Option(
        None, "--project-id", "-p", help="Project identifier (defaults to directory name)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Seed HMC memory from an existing project.

    Scans the project directory for:
    - persona.md (persona attributes and voice examples)
    - Dependency files (requirements.txt, pyproject.toml, package.json)
    - Source files (*.py, *.js, *.ts, *.md)

    Example:
        hmc seed .
        hmc seed /path/to/project --verbose
        hmc seed . --memory-dir /custom/path --project-id my-project
    """
    try:
        stats = seed_project(
            project_path=path, memory_dir=memory_dir, project_id=project_id, verbose=verbose
        )

        if not verbose:
            # Summary output when not verbose
            typer.secho("✅ Seeding complete!", fg=typer.colors.GREEN, bold=True)
            typer.echo(f"   Files: {stats['files_processed']}")
            typer.echo(f"   Chunks: {stats['code_chunks']}")
            typer.echo(f"   Persona facts: {stats['persona_facts']}")
            typer.echo(f"   Persona voices: {stats['persona_voices']}")
            if stats["warnings"]:
                typer.secho(f"   ⚠ Warnings: {len(stats['warnings'])}", fg=typer.colors.YELLOW)

    except SeederError as e:
        typer.secho(f"❌ Seeding failed: {e}", fg=typer.colors.RED, err=True)
        if e.file_path:
            typer.secho(f"   File: {e.file_path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        typer.secho("\n⚠ Seeding interrupted by user", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=130)
    except Exception as e:
        typer.secho(f"❌ Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
