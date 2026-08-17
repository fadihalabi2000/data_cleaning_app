from pathlib import Path


def test_official_uossm_logo_asset_exists():
    logo = Path(__file__).parent / "assets" / "uossm-logo-alt.png"
    assert logo.exists()
    assert logo.stat().st_size > 1000


def test_uossm_brand_uses_official_colors():
    source = (Path(__file__).parent / "app_quality8.py").read_text(encoding="utf-8")
    assert "#F36F3A" in source
    assert 'Helvetica Neue' in source
    assert "uossm-logo-alt.png" in source
