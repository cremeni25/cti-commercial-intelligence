from services.legacy_docx_conversion_manifest import CONVERSIONS, conversion_for_equipment
from services.proposal_template_catalog import TEMPLATES, template_for_equipment


def test_three_legacy_models_have_verified_docx_conversions():
    assert len(CONVERSIONS) == 3
    assert {item.equipment for item in CONVERSIONS} == {"CITIMAX 500", "XARIOS 350", "XARIOS 6"}
    assert all(item.converted_filename.endswith(".docx") for item in CONVERSIONS)
    assert all(item.expected_pages == 4 for item in CONVERSIONS)
    assert all(item.visual_review_approved for item in CONVERSIONS)
    assert all(item.preserves_equipment_image for item in CONVERSIONS)
    assert all(item.preserves_carrier_branding for item in CONVERSIONS)
    assert all(item.preserves_tables_and_pagination for item in CONVERSIONS)


def test_catalog_no_longer_exposes_legacy_doc_sources():
    assert len(TEMPLATES) == 16
    assert all(item.source_filename.lower().endswith(".docx") for item in TEMPLATES)
    for equipment in ("CITIMAX 500", "XARIOS 350", "XARIOS 6"):
        conversion = conversion_for_equipment(equipment)
        template = template_for_equipment(equipment)
        assert conversion is not None
        assert template.source_filename == conversion.converted_filename
        assert len(conversion.legacy_sha256) == 64
        assert len(conversion.converted_sha256) == 64
