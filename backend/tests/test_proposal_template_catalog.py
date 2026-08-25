import pytest

from services.proposal_template_catalog import (
    TEMPLATES,
    VARIANT_TEMPLATES,
    normalize_equipment,
    template_for_equipment,
)


def test_catalog_contains_exactly_sixteen_official_templates():
    assert len(TEMPLATES) == 16
    assert len({item.code for item in TEMPLATES}) == 16
    assert len({item.equipment for item in TEMPLATES}) == 16
    assert all(item.preserves_original_layout for item in TEMPLATES)
    assert all(item.preserves_images for item in TEMPLATES)
    assert all(item.preserves_carrier_branding for item in TEMPLATES)


def test_catalog_contains_four_official_commercial_ae_variants():
    assert {item.equipment for item in VARIANT_TEMPLATES} == {
        "CITIMAX 400AE",
        "CITIMAX 500AE",
        "CITIMAX D6AE",
        "CITIMAX D7AE",
    }


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("Citimax 280", "CITIMAX 280"),
        ("Citimax D6", "CITIMAX D6"),
        ("Citimax D7AE", "CITIMAX D7AE"),
        ("Citimax D7 AE", "CITIMAX D7AE"),
        ("Citimax D6 AE", "CITIMAX D6AE"),
        ("Citimax 400 AE", "CITIMAX 400AE"),
        ("Citimax 500 AE", "CITIMAX 500AE"),
        ("S 8", "S8"),
        ("S 9", "S9"),
        ("Vector HE 19", "VECTOR HE19"),
        ("X4-7500", "X4 7500"),
        ("X4-7700", "X4 7700"),
    ],
)
def test_equipment_normalization(input_value: str, expected: str):
    assert normalize_equipment(input_value) == expected
    assert template_for_equipment(input_value).equipment == expected


def test_d7ae_keeps_its_own_document_identity():
    template = template_for_equipment("CITIMAX D7AE")
    assert template.code == "CITIMAX_D7AE"
    assert template.equipment == "CITIMAX D7AE"
    assert template.source_filename == "CITIMAX D7 Rev 19.05.docx"


def test_unknown_equipment_is_rejected():
    with pytest.raises(ValueError, match="sem modelo oficial"):
        template_for_equipment("MODELO INEXISTENTE")
