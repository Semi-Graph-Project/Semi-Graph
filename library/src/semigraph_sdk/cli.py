"""Workspace-local Docker bootstrap for a dedicated SDK database."""

from __future__ import annotations

import argparse
import secrets
import socket
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import yaml

from .config import ConfigError, SDKConfig
from .database import SetupError
from .engine import Engine


class CLIError(RuntimeError):
    """A CLI setup precondition failed."""


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def init_workspace(workspace: str | Path, *, http_port: int = 17474, bolt_port: int = 17687) -> Path:
    """Create independent config, secrets and Compose files without overwriting."""
    if http_port == bolt_port:
        raise CLIError("HTTP and Bolt ports must differ")
    path = Path(workspace).expanduser().resolve()
    outputs = ("semigraph.yaml", "compose.yaml", ".env", ".gitignore")
    conflicts = [name for name in outputs if (path / name).exists()]
    if conflicts:
        raise CLIError(f"Workspace files already exist; refusing to overwrite: {conflicts}")
    if path.exists() and not path.is_dir():
        raise CLIError(f"Workspace is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    workspace_id = f"semigraphsdk-{secrets.token_hex(6)}"
    password = secrets.token_urlsafe(32)
    config = {
        "workspace_id": workspace_id,
        "database": {
            "uri": f"bolt://127.0.0.1:{bolt_port}",
            "user": "neo4j",
            "name": "neo4j",
            "password_key": "NEO4J_PASSWORD",
        },
        "embedding": {
            "model": "BAAI/bge-base-en-v1.5",
            "revision": "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
            "dimension": 768,
            "normalize": True,
            "device": "cpu",
        },
        "secrets_file": ".env",
    }
    compose = files("semigraph_sdk").joinpath("deployment/compose.yaml").read_text(
        encoding="utf-8"
    )
    contents = {
        "semigraph.yaml": yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        "compose.yaml": compose,
        ".env": (
            f"COMPOSE_PROJECT_NAME={workspace_id}\n"
            f"SDK_HTTP_PORT={http_port}\n"
            f"SDK_BOLT_PORT={bolt_port}\n"
            f"NEO4J_PASSWORD={password}\n"
        ),
        ".gitignore": ".env\n",
    }
    created: list[Path] = []
    try:
        for name in outputs:
            target = path / name
            with target.open("x", encoding="utf-8") as handle:
                handle.write(contents[name])
            created.append(target)
        (path / ".env").chmod(0o600)
    except OSError:
        for target in created:
            target.unlink(missing_ok=True)
        raise
    return path


def _compose(config: SDKConfig) -> list[str]:
    workspace = config.config_path.parent
    compose_file = workspace / "compose.yaml"
    if not compose_file.is_file():
        raise CLIError(f"Missing Compose file: {compose_file}")
    return [
        "docker", "compose", "--project-name", config.workspace_id,
        "--env-file", str(config.secrets_file), "-f", str(compose_file),
    ]


def _docker(args: list[str], *, cwd: Path) -> str:
    try:
        result = subprocess.run(
            args, cwd=cwd, check=True, capture_output=True, text=True
        )
    except FileNotFoundError as exc:
        raise CLIError("Docker Compose is not installed or not on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).strip()
        raise CLIError(f"Docker Compose failed: {detail}") from exc
    return result.stdout.strip()


def _assert_port_available(port: int) -> None:
    with socket.socket() as probe:
        # A recently stopped Docker proxy can leave connections in TIME_WAIT.
        # Reusing the address ignores that transient state while bind still
        # fails when another service is actively listening on the port.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise CLIError(
                f"Local port {port} is occupied; choose new --http-port/--bolt-port "
                "in a new workspace, or edit both .env and semigraph.yaml"
            ) from exc


def db_up(workspace: str | Path):
    path = Path(workspace).expanduser().resolve()
    config = SDKConfig.from_file(path / "semigraph.yaml")
    command = _compose(config)
    # A generated workspace always points to its own local Bolt mapping.
    secrets_lines = config.secrets_file.read_text(encoding="utf-8").splitlines()
    values = dict(line.split("=", 1) for line in secrets_lines if "=" in line)
    try:
        http_port = _port(values["SDK_HTTP_PORT"])
        bolt_port = _port(values["SDK_BOLT_PORT"])
    except (KeyError, argparse.ArgumentTypeError) as exc:
        raise CLIError("Missing or invalid SDK ports in workspace .env") from exc
    if config.database.uri != f"bolt://127.0.0.1:{bolt_port}":
        raise CLIError("Config database.uri differs from this workspace's Docker Bolt port")
    if values.get("COMPOSE_PROJECT_NAME") != config.workspace_id:
        raise CLIError("Compose project name differs from config workspace_id")
    _docker(command + ["config", "--quiet"], cwd=path)
    running = _docker(command + ["ps", "--status", "running", "-q", "neo4j"], cwd=path)
    if not running:
        _assert_port_available(http_port)
        _assert_port_available(bolt_port)
    _docker(
        command + ["up", "-d", "--wait", "--wait-timeout", "300", "neo4j"],
        cwd=path,
    )
    with Engine(config) as engine:
        return engine.setup()


def db_down(workspace: str | Path) -> None:
    path = Path(workspace).expanduser().resolve()
    config = SDKConfig.from_file(path / "semigraph.yaml")
    _docker(_compose(config) + ["down"], cwd=path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semigraph-sdk")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Create an isolated database workspace")
    init.add_argument("workspace")
    init.add_argument("--http-port", type=_port, default=17474)
    init.add_argument("--bolt-port", type=_port, default=17687)
    db = commands.add_parser("db", help="Manage the SDK database")
    db_commands = db.add_subparsers(dest="db_command", required=True)
    up = db_commands.add_parser("up", help="Start Docker and prepare schema/indexes")
    up.add_argument("--workspace", required=True)
    down = db_commands.add_parser("down", help="Stop this workspace and keep its data")
    down.add_argument("--workspace", required=True)
    setup = db_commands.add_parser("setup", help="Prepare an existing dedicated Neo4j")
    setup.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            path = init_workspace(
                args.workspace, http_port=args.http_port, bolt_port=args.bolt_port
            )
            print(f"Created SDK workspace: {path}")
            print(f"Next: semigraph-sdk db up --workspace {path}")
            return 0
        if args.db_command == "up":
            report = db_up(args.workspace)
        elif args.db_command == "down":
            db_down(args.workspace)
            print("Stopped SDK database; workspace data volumes are preserved")
            return 0
        else:
            with Engine.from_config(args.config) as engine:
                report = engine.setup()
        print(
            f"Ready: {report.database} at {report.uri}; "
            f"APOC {report.apoc_version}, GDS {report.gds_version}; "
            f"vector indexes ONLINE (dim={report.embedding_dimension}); "
            f"search_ready={report.search_ready}"
        )
        return 0
    except (CLIError, ConfigError, SetupError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
