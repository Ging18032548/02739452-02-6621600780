import pytest
from dags.utils.transformers import transform_and_normalize
from dags.utils.quality_checks import validate_data_quality

def test_transform_and_normalize():
    raw = [{"source": "OAE", "product": " ข้าวเจ้า ", "price": "12000", "unit": "บาท/ตัน", "date": "2026-10-23"}]
    res = transform_and_normalize(raw)
    assert len(res) == 1
    assert res[0]["product_name"] == "ข้าวเจ้า"
    assert res[0]["price_value"] == 12000.0

def test_validate_data_quality():
    records = [
        {"price_value": 100, "reported_date": "2026-10-23", "product_name": "ข้าว"},
        {"price_value": -10, "reported_date": "2026-10-23", "product_name": "ข้าว"}
    ]
    passed, rejected = validate_data_quality(records)
    assert len(passed) == 1
    assert len(rejected) == 1