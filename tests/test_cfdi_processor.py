from pathlib import Path

from cfdi_processor import iter_rows, parse_cfdi_file


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_cfdi_40_concept_rows():
    parsed = parse_cfdi_file(FIXTURES / "cfdi40_min.xml")
    rows = list(iter_rows(parsed, granularity="concept"))
    assert len(rows) == 1
    assert rows[0]["UUID"] == "11111111-1111-1111-1111-111111111111"
    assert rows[0]["Emisor_RFC"] == "AAA010101AAA"
    assert rows[0]["Receptor_RFC"] == "BBB010101BBB"


def test_parse_cfdi_33_namespace_detection():
    parsed = parse_cfdi_file(FIXTURES / "cfdi33_min.xml")
    rows = list(iter_rows(parsed, granularity="invoice"))
    assert len(rows) == 1
    assert rows[0]["UUID"] == "22222222-2222-2222-2222-222222222222"
    assert rows[0]["Moneda"] == "MXN"

