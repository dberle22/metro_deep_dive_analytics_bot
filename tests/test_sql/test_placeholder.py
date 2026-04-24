from pathlib import Path


def test_sql_phase2_placeholder_removed() -> None:
    content = Path("app/query/generator.py").read_text(encoding="utf-8")
    assert "placeholder" not in content.lower()
