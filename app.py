import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt

# Firebase'i başlat
if not firebase_admin._apps:
    cred = credentials.Certificate("/mnt/data/scregproject-firebase-adminsdk-fbsvc-4425e27c65.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Streamlit ayarları
st.set_page_config(page_title="Kafe Dashboard", layout="wide")

# Stil
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    html, body, .stApp {
        background-color: #392315;
        color: #f5d9c7;
        font-family: 'Poppins', sans-serif;
        font-size: 14px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffe8d6;
        font-size: 18px;
    }
    .card {
        background: rgba(74, 44, 23, 0.7);
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
        backdrop-filter: blur(3px);
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 10px;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0px 6px 15px rgba(0,0,0,0.3);
    }
    .card-title {
        text-align: center;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    p {
        font-size: 13px;
        margin: 0;
    }
    .metric-card {
        margin-top: 5px;
        margin-bottom: 10px;
    }
    footer {
        text-align: center;
        margin-top: 1rem;
        font-size: 12px;
        color: #d4a373;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("☕ Menü")
    selected_date = st.date_input("Tarih Seçiniz", datetime.today())

def get_orders_by_date(date_str):
    orders_ref = db.collection('orders').document(date_str).collection('userOrders')
    docs = orders_ref.stream()
    orders = []
    for doc in docs:
        orders.append(doc.to_dict())
    return orders

def calculate_total(orders):
    total = 0
    product_counter = {}
    for order in orders:
        for item in order.get("items", []):
            name = item.get("name")
            quantity = int(item.get("quantity", 0))
            price = float(item.get("price", 0))
            total += quantity * price
            product_counter[name] = product_counter.get(name, 0) + quantity
    return total, product_counter

selected_date_str = selected_date.strftime('%Y-%m-%d')
yesterday_str = (selected_date - timedelta(days=1)).strftime('%Y-%m-%d')

# Firestore verisi
if 'data' not in st.session_state:
    st.session_state.data = {}

today_orders = get_orders_by_date(selected_date_str)
yesterday_orders = get_orders_by_date(yesterday_str)

st.session_state.data[selected_date_str] = today_orders

# Günlük hesaplamalar
today_total, today_products = calculate_total(today_orders)
yesterday_total, _ = calculate_total(yesterday_orders)

growth_percentage = ((today_total - yesterday_total) / yesterday_total * 100) if yesterday_total > 0 else 0

if today_products:
    best_product_name, best_product_quantity = max(today_products.items(), key=lambda x: x[1])
else:
    best_product_name, best_product_quantity = "-", 0

# Başlık ve metrik kartlar
st.title("☕ Kafe Satış Dashboard")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4, gap="large")

with col1:
    st.markdown(f'<div class="card"><div class="card-title">📈 Günlük Ciro</div><p style="text-align:center;">{today_total:.2f} ₺</p></div>', unsafe_allow_html=True)
with col2:
    change_icon = "📈" if growth_percentage >= 0 else "📉"
    st.markdown(f'<div class="card"><div class="card-title">{change_icon} Değişim %</div><p style="text-align:center;">{growth_percentage:.2f}%</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="card"><div class="card-title">🛒 En Çok Satan</div><p style="text-align:center;">{best_product_name} ({best_product_quantity} adet)</p></div>', unsafe_allow_html=True)
with col4:
    total_items = sum(today_products.values()) if today_products else 0
    st.markdown(f'<div class="card"><div class="card-title">📦 Toplam Satış</div><p style="text-align:center;">{total_items} Adet</p></div>', unsafe_allow_html=True)

# Grafikler
if today_products:
    st.markdown("<br>", unsafe_allow_html=True)
    col5, col6 = st.columns(2, gap="large")

    with col5:
        st.markdown('<div class="metric-card"><h3 style="text-align:center;">📊 Ürün Satış Dağılımı</h3>', unsafe_allow_html=True)
        df_bar = pd.DataFrame({'Kahve': list(today_products.keys()), 'Adet': list(today_products.values())})
        fig_bar = px.bar(df_bar, x='Kahve', y='Adet', color_discrete_sequence=['#d4a373'], template="plotly_dark")
        fig_bar.update_layout(plot_bgcolor='rgba(74,44,23,0.7)', paper_bgcolor='rgba(74,44,23,0.7)',
                              font_color='#f5d9c7', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                              margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col6:
        st.markdown('<div class="metric-card"><h3 style="text-align:center;">📈 Son 30 Gün Ciro Trend</h3>', unsafe_allow_html=True)
        trends = []
        for i in range(30):
            date_i = selected_date - timedelta(days=i)
            date_str_i = date_i.strftime('%Y-%m-%d')
            orders_i = get_orders_by_date(date_str_i)
            total_i, _ = calculate_total(orders_i)
            trends.append({'Tarih': date_str_i, 'Ciro': total_i})
        df_line = pd.DataFrame(trends[::-1])
        fig_line = px.line(df_line, x='Tarih', y='Ciro', markers=True, color_discrete_sequence=['#7f5539'], template="plotly_dark")
        fig_line.update_layout(plot_bgcolor='rgba(74,44,23,0.7)', paper_bgcolor='rgba(74,44,23,0.7)',
                               font_color='#f5d9c7', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                               margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

        # SARIMA tahmini
        st.markdown('<div class="metric-card"><h3 style="text-align:center;">🔮 Gelecek 7 Gün Tahmini (SARIMA)</h3>', unsafe_allow_html=True)
        df_line['Tarih'] = pd.to_datetime(df_line['Tarih'])
        df_line.set_index('Tarih', inplace=True)
        model = SARIMAX(df_line['Ciro'], order=(1,1,1), seasonal_order=(1,1,1,7))
        results = model.fit(disp=False)
        forecast = results.get_forecast(steps=7)
        forecast_df = forecast.summary_frame()
        forecast_df['Tarih'] = [df_line.index[-1] + timedelta(days=i+1) for i in range(7)]

        df_forecast = pd.DataFrame({
            'Tarih': forecast_df['Tarih'],
            'Ciro': forecast_df['mean'],
            'Tür': ['Tahmin']*7
        })
        df_combined = pd.concat([
            df_line.reset_index().iloc[-7:][['Tarih', 'Ciro']].assign(Tür='Gerçek'),
            df_forecast
        ])
        fig_forecast = px.line(df_combined, x='Tarih', y='Ciro', color='Tür', markers=True,
                               color_discrete_map={'Gerçek': '#d4a373', 'Tahmin': '#9c6644'}, template="plotly_dark")
        fig_forecast.update_layout(plot_bgcolor='rgba(74,44,23,0.7)', paper_bgcolor='rgba(74,44,23,0.7)',
                                   font_color='#f5d9c7', margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_forecast, use_container_width=True)
