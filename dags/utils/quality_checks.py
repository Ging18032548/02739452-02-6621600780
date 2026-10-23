import logging

def validate_data_quality(records):
    """
    ฟังก์ชันตรวจสอบคุณภาพข้อมูล (Data Quality Validation & Branching)
    ทำหน้าที่ตรวจสอบความถูกต้องของข้อมูลราคาสินค้าเกษตรจากทุกแหล่ง
    โดยคัดกรองเรคอร์ดที่ผิดพลาด (Rejected) ออก และเก็บเฉพาะเรคอร์ดที่ถูกต้อง (Passed)
    """
    passed = []
    rejected = []
    
    if not records:
        logging.warning("No records received for quality validation.")
        return passed, rejected

    for r in records:
        try:
            # ดึงค่าฟิลด์สำคัญมาตรวจสอบ
            price = r.get("price_value")
            product_name = r.get("product_name")
            reported_date = r.get("reported_date")
            source_name = r.get("source_name")
            
            # เงื่อนไขการตรวจสอบคุณภาพ (Data Quality Rules)
            # 1. ราคาต้องมีค่ามากกว่า 0
            # 2. ต้องมีชื่อสินค้า (product_name)
            # 3. ต้องมีวันที่รายงาน (reported_date)
            # 4. ต้องมีระบุแหล่งที่มาของข้อมูล (source_name)
            if price is not None and float(price) > 0 and product_name and reported_date and source_name:
                passed.append(r)
            else:
                rejected.append({
                    "record": r, 
                    "reason": "Validation Failed: Price <= 0, missing product_name, missing reported_date, or missing source_name"
                })
        except Exception as e:
            rejected.append({
                "record": r, 
                "reason": f"Exception during validation processing: {str(e)}"
            })
            
    # บันทึก Log สรุปผลการตรวจสอบคุณภาพข้อมูล
    logging.info(f"--- Data Quality Check Summary ---")
    logging.info(f"Total Processed Records: {len(records)}")
    logging.info(f"Passed Quality Check: {len(passed)}")
    logging.info(f"Rejected Records: {len(rejected)}")
    
    return passed, rejected