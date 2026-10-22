import shutil
import zipfile

import pytest

from g4agent.package import build_zip, validate
from g4agent.paths import AGENT


def test_agent_dir_is_valid():
    assert validate(AGENT) == "gemma-4-31b-it-qat-w4a16-ct"


def test_zip_has_agent_yaml_at_root(tmp_path):
    archive = build_zip(AGENT, tmp_path / "submission.zip")
    with zipfile.ZipFile(archive) as zf:
        assert "agent.yaml" in zf.namelist()


def test_two_base_models_are_rejected(tmp_path):
    agent = tmp_path / "agent"
    shutil.copytree(AGENT, agent)
    sub = agent / "sub_agents" / "code_analyzer.yaml"
    sub.write_text(sub.read_text().replace("gemma-4-31b-it-qat-w4a16-ct",
                                           "gemma-4-12b-it-qat-w4a16-ct"))
    with pytest.raises(ValueError, match="exactly one"):
        validate(agent)


def test_disallowed_extension_is_rejected(tmp_path):
    agent = tmp_path / "agent"
    shutil.copytree(AGENT, agent)
    (agent / "weights.bin").write_bytes(b"\0")
    with pytest.raises(ValueError, match="extension"):
        validate(agent)
