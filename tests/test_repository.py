"""Apply the distributed contract to the actual development documents."""

from pathlib import Path

from taolib.documents import validate


def test_development_documents_use_the_shared_runtime_contract():
    root = Path(__file__).resolve().parents[1]
    result = validate(root, list((root / "docs").rglob("*.md")))
    assert result.valid, result.to_dict()
