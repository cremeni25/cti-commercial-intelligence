from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LegacyDocxConversion:
    equipment: str
    legacy_filename: str
    converted_filename: str
    legacy_sha256: str
    converted_sha256: str
    expected_pages: int
    visual_review_approved: bool = True
    preserves_equipment_image: bool = True
    preserves_carrier_branding: bool = True
    preserves_tables_and_pagination: bool = True


CONVERSIONS: tuple[LegacyDocxConversion, ...] = (
    LegacyDocxConversion(
        equipment="CITIMAX 500",
        legacy_filename="CITIMAX 500.doc",
        converted_filename="CITIMAX 500.docx",
        legacy_sha256="1db3de00d53def4f9d4b6eee2921f9b06313416c554636932b6a552c3aa350d8",
        converted_sha256="f8413f72e3258936c70ccd419ebf5e4bb918156f41340141f57222d67694138e",
        expected_pages=4,
    ),
    LegacyDocxConversion(
        equipment="XARIOS 350",
        legacy_filename="XARIOS 350.doc",
        converted_filename="XARIOS 350.docx",
        legacy_sha256="47e2018e7916d42d2449667d4dc1861bc81b1dd07325d6acba5b73521ba79fff",
        converted_sha256="15c7224e8d2310b5b5ca51818f881ba672bee5ea8a7a4584ddc878cdec6f2456",
        expected_pages=4,
    ),
    LegacyDocxConversion(
        equipment="XARIOS 6",
        legacy_filename="XARIOS 6.doc",
        converted_filename="XARIOS 6.docx",
        legacy_sha256="b009c43eca92abbe428e4ea88e749acd50dbdb5d8d4ae960209df09baedc5072",
        converted_sha256="e9cb32623c555bf8d259502849a76c0b2b10a50b1a5ee766bb74e122450433af",
        expected_pages=4,
    ),
)


_BY_EQUIPMENT = {item.equipment: item for item in CONVERSIONS}


def conversion_for_equipment(equipment: str) -> LegacyDocxConversion | None:
    return _BY_EQUIPMENT.get(equipment.strip().upper())
