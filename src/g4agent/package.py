"""Validate the agent directory exactly as the official notebook does, then zip it.

The checks come from the harness itself (`adk_submission`, `swegemma.config`), so a directory
that passes here compiles on the scorer: declarative YAML only, one base model from the allowed
list, allowed extensions, no symlinks, under 3 GiB unpacked.
"""

import shutil
import zipfile
from pathlib import Path

from adk_submission import validate_directory
from adk_submission.discovery import discover_declared_models
from swegemma.config import (
    ALLOWED_SUBMISSION_EXTENSIONS,
    MAX_SUBMISSION_SIZE_BYTES,
    build_submission_limits,
)

ALLOWED_MODELS = frozenset({
    "gemma-4-31b-it-qat-w4a16-ct",
    "gemma-4-12b-it-qat-w4a16-ct",
    "gemma-4-e4b-it-qat-w4a16-ct",
    "gemma-4-e2b-it-qat-w4a16-ct",
})


def declared_model(agent_dir: Path) -> str:
    models = discover_declared_models(agent_dir)
    if len(models) != 1:
        raise ValueError(f"expected exactly one declared model, got {sorted(models)}")
    model = next(iter(models))
    if model not in ALLOWED_MODELS:
        raise ValueError(f"model {model!r} is not allowed; allowed: {sorted(ALLOWED_MODELS)}")
    return model


def validate(agent_dir: Path) -> str:
    """Raise on anything the scorer would reject; return the declared base model."""
    for path in agent_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlinks are not permitted: {path.relative_to(agent_dir)}")
        if path.is_file() and path.suffix.lower() not in ALLOWED_SUBMISSION_EXTENSIONS:
            raise ValueError(f"disallowed file extension: {path.relative_to(agent_dir)}")
    limits, _ = build_submission_limits()
    validate_directory(agent_dir, limits=limits)
    return declared_model(agent_dir)


def build_zip(agent_dir: Path, out: Path) -> Path:
    """Write out (a .zip) with agent.yaml at the archive root, after validation."""
    validate(agent_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    archive = Path(shutil.make_archive(str(out.with_suffix("")), "zip", root_dir=agent_dir))
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        total = sum(i.file_size for i in zf.infolist())
    if "agent.yaml" not in names:
        raise ValueError("agent.yaml is not at the root of the archive")
    if total > MAX_SUBMISSION_SIZE_BYTES:
        raise ValueError(f"archive exceeds 3 GiB unpacked: {total} bytes")
    return archive
