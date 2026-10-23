import streamlit as st
import pandas as pd
import psycopg2
import os
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Agricultural Price Intelligence Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS สำหรับตกแต่งหน้าเว็บ
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .header-container {
            background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
            padding: 25px;
            border-radius: 12px;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            padding: 15px;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# 3. เชื่อมต่อฐานข้อมูลและโหลดข้อมูล
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "airflow_db"),
        user=os.getenv("DB_USER", "airflow"),
        password=os.getenv("DB_PASSWORD", "airflow"),
        port=int(os.getenv("DB_PORT", 5432))
    )

def load_data():
    try:
        conn = init_connection()
        query = """
            SELECT id, source_name, source_record_id, product_type, product_name, 
                   market_name, province, reported_date, price_min, price_max, 
                   price_value, unit, currency, source_url, collected_at, updated_at
            FROM agricultural_prices
            ORDER BY reported_date DESC;
        """
        df = pd.read_sql(query, conn)
        df['reported_date'] = pd.to_datetime(df['reported_date'])
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

# 4. Header ส่วนหัวของ Dashboard
st.markdown("""
    <div class="header-container">
        <h1 style="margin:0; font-size:26px;">🌾 ระบบสารสนเทศและวิเคราะห์ราคาสินค้าเกษตรไทย</h1>
        <p style="margin:5px 0 0 0; font-size:14px; opacity:0.9;">Multi-Source ETL Pipeline & Real-Time Price Analytics Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# 5. KPI Metrics สถิติภาพรวมทั้งหมด
if not df.empty:
    total_records = len(df)
    avg_price = df["price_value"].mean()
    max_price = df["price_value"].max()
    min_price = df["price_value"].min()
    unique_sources = df["source_name"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📊 จำนวนรายการ", f"{total_records:,} รายการ")
    c2.metric("💰 ราคาเฉลี่ยรวม", f"{avg_price:,.2f} ฿")
    c3.metric("📈 ราคาสูงสุด", f"{max_price:,.2f} ฿")
    c4.metric("📉 ราคาต่ำสุด", f"{min_price:,.2f} ฿")
    c5.metric("🔗 แหล่งข้อมูล", f"{unique_sources} แหล่ง")
    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Charts Section (กราฟแสดงผลเต็มหน้าจอ)
    st.markdown("### 📈 การวิเคราะห์แนวโน้มและเปรียบเทียบราคา")
    
    col_1, col_2 = st.columns(2)
    with col_1:
        fig_bar = px.bar(
            df, x="product_name", y="price_value", color="source_name",
            title="เปรียบเทียบราคาสินค้าเกษตรแยกตามแหล่งข้อมูล",
            labels={"product_name": "สินค้า", "price_value": "ราคา (บาท)", "source_name": "แหล่งข้อมูล"},
            barmode="group", template="plotly_white"
        )
        fig_bar.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_2:
        fig_line = px.line(
            df.sort_values("reported_date"), x="reported_date", y="price_value", color="product_name",
            title="แนวโน้มราคาตามช่วงเวลา (Time-Series Trend)",
            labels={"reported_date": "วันที่รายงาน", "price_value": "ราคา (บาท)", "product_name": "สินค้า"},
            template="plotly_white"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # 7. Summary Table by Product
    st.markdown("### 📊 ตารางสรุปสถิติราคาแยกตามรายสินค้า")
    summary_table = df.groupby("product_name").agg(
        จำนวนเรคอร์ด=("price_value", "count"),
        ราคาเฉลี่ย=("price_value", "mean"),
        ราคาสูงสุด=("price_value", "max"),
        ราคาต่ำสุด=("price_value", "min")
    ).reset_index()
    summary_table["ราคาเฉลี่ย"] = summary_table["ราคาเฉลี่ย"].round(2)
    summary_table["ราคาสูงสุด"] = summary_table["ราคาสูงสุด"].round(2)
    summary_table["ราคาต่ำสุด"] = summary_table["ราคาต่ำสุด"].round(2)
    st.dataframe(summary_table, use_container_width=True)

    # 8. Main Raw Data Table & Export
    st.markdown("---")
    st.markdown("### 📋 รายละเอียดข้อมูลทั้งหมดในระบบ")
    display_cols = ["id", "source_name", "product_type", "product_name", "market_name", "reported_date", "price_value", "unit", "source_url"]
    st.dataframe(df[display_cols], use_container_width=True)
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 ดาวน์โหลดข้อมูลทั้งหมดเป็น CSV",
        data=csv_data,
        file_name='agricultural_prices_full_export.csv',
        mime='text/csv'
    )
else:
    st.info("ยังไม่มีข้อมูลในระบบ กรุณารัน ETL Pipeline ในหน้า Apache Airflow เพื่อนำเข้าข้อมูล")