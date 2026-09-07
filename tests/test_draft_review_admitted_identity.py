import json
import subprocess
import sys
from copy import deepcopy
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("materializer", ROOT / "scripts/materialize_draft_review_identity_admission.py")
m = module_from_spec(spec)
spec.loader.exec_module(m)


def test_replay_preserves_original_rows_and_only_adds_four():
    result = m.build()
    assert result == json.loads((ROOT / m.OUTPUT_PATH).read_bytes())
    original = json.loads(m.historical(m.OUTPUT_PATH))
    assert result["records"][:68] == original["records"]
    assert len(result["records"]) == 72


def test_legacy_cli_cannot_discard_accepted_extension(tmp_path):
    output = tmp_path / "crosswalk.json"
    result = subprocess.run([sys.executable, "scripts/promote_identity_crosswalk_rows.py",
                             "--forge-artifact", "unused.json", "--out", str(output)],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode != 0
    assert "would discard accepted rows" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("kind", ["status", "extra_edge", "tier", "scope", "source", "acceptance"])
def test_materializer_rejects_unaccepted_drift(kind):
    receipt = json.loads((ROOT / m.RECEIPT_PATH).read_bytes())
    if kind == "status": receipt["status"] = "proposed"
    if kind == "extra_edge": receipt["identity_records"].append(deepcopy(receipt["identity_records"][0]))
    if kind == "tier": receipt["identity_records"][0]["confidence"] = "high"
    if kind == "scope": receipt["consumer_scope"]["weeks"] = [1, 22]
    if kind == "source": receipt["sources"][0]["sha256"] = "0" * 64
    if kind == "acceptance": receipt["operator_acceptance"] = "invented"
    with pytest.raises(ValueError): m.build(receipt)


@pytest.mark.parametrize("field", ["schema_version", "scope", "proposal_path", "review",
                                   "merge_authorized", "production_deployment_authorized", "unknown_authority"])
def test_contradictory_authority_envelope_rejected(field):
    receipt = json.loads((ROOT / m.RECEIPT_PATH).read_bytes())
    receipt[field] = True
    with pytest.raises(ValueError, match="authority envelope"):
        m.build(receipt)
