import pandas as pd

def transform_and_normalize(raw_data_list):
    """แปลงข้อมูลและ Normalize ให้อยู่ใน Unified Schema เดียวกัน"""
    cleaned_records = []
    for item in raw_data_list:
        try:
            record = {
                "source_name": item.get("source"),
                "product_type": item.get("product_type", "พืชเศรษฐกิจ"),
                "product_name": item.get("product").strip(),
                "market_name": item.get("market", "ตลาดกลางประเทศไทย"),
                "province": item.get("province"),
                "reported_date": pd.to_datetime(item.get("date")).date(),
                "price_min": float(item.get("price")) * 0.95,  # ราคาต่ำสุดจำลอง
                "price_max": float(item.get("price")) * 1.05,  # ราคาสูงสุดจำลอง
                "price_value": float(item.get("price")),
                "unit": item.get("unit"),
                "currency": item.get("currency", "THB"),
                "source_url": item.get("source_url")
            }
            cleaned_records.append(record)
        except Exception:
            continue
    return cleaned_records