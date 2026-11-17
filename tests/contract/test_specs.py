import re
from pathlib import Path

SPECS = Path(__file__).resolve().parents[2] / "docs/specs"
STATES = {"implementiert", "offen"}


def test_product_specs_have_unique_ids_status_and_evidence() -> None:
    sections = (SPECS / "produkt.md").read_text(encoding="utf-8").split("\n## ")[1:]
    seen = set()
    assert sections
    for section in sections:
        heading = section.splitlines()[0]
        spec_id, title = heading.split(" ", 1)
        assert re.fullmatch(r"DS-\d{3}", spec_id) and title.strip(), heading
        assert spec_id not in seen, spec_id
        seen.add(spec_id)
        statuses = re.findall(r"^Status: (.+)$", section, re.MULTILINE)
        assert len(statuses) == 1 and statuses[0] in STATES, spec_id
        if statuses[0] == "implementiert":
            for label in ("Umsetzung", "Prüfung"):
                link = re.search(rf"{label}: \[[^\]]+\]\(([^)]+)\)", section)
                assert link and (SPECS / link[1]).is_file(), (spec_id, label)


def test_source_matrix_has_unique_ids_priorities_and_status() -> None:
    rows = (SPECS / "quellenmatrix.md").read_text(encoding="utf-8").splitlines()
    seen = set()
    groups = set()
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) < 2 or cells[1] not in {"MUSS", "SOLL", "KANN"}:
            continue
        spec_id = cells[0]
        assert re.fullmatch(r"[A-Z]+-\d{3}", spec_id), row
        assert spec_id not in seen and cells[-1] in STATES and cells[2], row
        seen.add(spec_id)
        groups.add(spec_id.split("-")[0])
    assert {"SRC", "QLT", "LIC", "TEC", "EVD", "COV", "OPS"} <= groups
