import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Sayfa Ayarları
st.set_page_config(page_title="Kafe Dashboard", layout="wide")

# Stil ve Fontlar
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
    refresh = st.button("🔄 Verileri Yenile")

# Kahve verisi
np.random.seed(42)
coffee_list = [
    "Espresso", "Americano", "Cappuccino", "Latte", "Mocha",
    "Flat White", "Macchiato", "Cortado", "Turkish Coffee", "Irish Coffee"
]
coffee_prices = {coffee: round(np.random.randint(100, 201, 1)[0] / 10) * 10 for coffee in coffee_list}

@st.cache_data
def generate_random_data():
    dates = pd.date_range(end=datetime.today(), periods=60).to_pydatetime().tolist()
    data = []
    coffee_mean_sales = {coffee: np.random.randint(0, 31) for coffee in coffee_list}
    
    for date in dates:
        daily_sales = {'date': date.strftime('%Y-%m-%d'), 'sales': []}
        for coffee in coffee_list:
            base_quantity = np.random.normal(coffee_mean_sales[coffee], 5)
            if date.weekday() in [5, 6]:
                base_quantity *= np.random.uniform(1.1, 1.3)
            quantity = max(0, int(base_quantity))
            daily_sales['sales'].append({'coffee': coffee, 'quantity': quantity, 'price': coffee_prices[coffee]})
        data.append(daily_sales)
    return data

if 'data' not in st.session_state or refresh:
    st.session_state.data = generate_random_data()

# Tarih ve veri alma
selected_date_str = selected_date.strftime('%Y-%m-%d')
yesterday_date = selected_date - timedelta(days=1)
yesterday_date_str = yesterday_date.strftime('%Y-%m-%d')

def get_day_data(date_str):
    for day in st.session_state.data:
        if day['date'] == date_str:
            return day
    return None

def calculate_total(day_data):
    if not day_data:
        return 0, {}
    total = 0
    product_counter = {}
    for item in day_data['sales']:
        total += item['quantity'] * item['price']
        product_counter[item['coffee']] = item['quantity']
    return total, product_counter

today_data = get_day_data(selected_date_str)
yesterday_data = get_day_data(yesterday_date_str)

today_total, today_products = calculate_total(today_data)
yesterday_total, _ = calculate_total(yesterday_data)

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
        trends = [{'Tarih': day['date'], 'Ciro': calculate_total(day)[0]} for day in st.session_state.data]
        df_line = pd.DataFrame(trends[-30:])
        fig_line = px.line(df_line, x='Tarih', y='Ciro', markers=True, color_discrete_sequence=['#7f5539'], template="plotly_dark")
        fig_line.update_layout(plot_bgcolor='rgba(74,44,23,0.7)', paper_bgcolor='rgba(74,44,23,0.7)',
                               font_color='#f5d9c7', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                               margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

# Haftalık analiz
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="metric-card"><h3 style="text-align:center;">🔮 Haftalık Satış Performansı</h3>', unsafe_allow_html=True)

today = datetime.today()
start_of_week = today - timedelta(days=today.weekday())
dates_of_week = [(start_of_week + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

real_sales = []
valid_dates = []
for date_str in dates_of_week:
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    if date_obj > today:
        continue
    day_data = get_day_data(date_str)
    if day_data:
        total, _ = calculate_total(day_data)
        real_sales.append(total)
        valid_dates.append(date_str)

# Ortalama değerler
weekday_totals = {i: [] for i in range(7)}
for day in st.session_state.data:
    date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
    weekday = date_obj.weekday()
    total, _ = calculate_total(day)
    weekday_totals[weekday].append(total)

weekday_averages = {i: np.mean(weekday_totals[i]) if weekday_totals[i] else 0 for i in range(7)}
expected_sales = [weekday_averages[datetime.strptime(d, '%Y-%m-%d').weekday()] for d in dates_of_week]

df_week = pd.DataFrame({
    'Tarih': valid_dates + dates_of_week,
    'Ciro': real_sales + expected_sales,
    'Tür': ['Gerçekleşen'] * len(valid_dates) + ['Beklenen'] * 7
})

fig_week = px.line(df_week, x='Tarih', y='Ciro', color='Tür', markers=True,
                   color_discrete_map={'Gerçekleşen': '#d4a373', 'Beklenen': '#9c6644'}, template="plotly_dark")
fig_week.update_layout(plot_bgcolor='rgba(74,44,23,0.7)', paper_bgcolor='rgba(74,44,23,0.7)',
                       font_color='#f5d9c7', xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
                       margin=dict(l=10, r=10, t=10, b=10), legend_title_text='Veri Türü')
st.plotly_chart(fig_week, use_container_width=True)

# Bugünün performansı
today_str = today.strftime('%Y-%m-%d')
if today_str in dates_of_week:
    index_today = dates_of_week.index(today_str)
    if index_today < len(real_sales):
        today_real = real_sales[index_today]
        today_expected = expected_sales[index_today]
        difference_percentage = ((today_real - today_expected) / today_expected * 100) if today_expected > 0 else 0
        if difference_percentage >= 0:
            st.success(f"🎯 Bugün beklenenden %{difference_percentage:.1f} fazla satış yapıldı!")
        else:
            st.error(f"⚠️ Bugün beklenenden %{abs(difference_percentage):.1f} daha az satış yapıldı.")
else:
    st.info("Bugün haftalık dönem dışında.")

# 30 günlük karşılaştırma
today = datetime.today()
last_30_days = today - timedelta(days=30)
prev_30_days = today - timedelta(days=60)

recent_sales = {coffee: 0 for coffee in coffee_list}
previous_sales = {coffee: 0 for coffee in coffee_list}

for day in st.session_state.data:
    date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
    for sale in day['sales']:
        if last_30_days <= date_obj <= today:
            recent_sales[sale['coffee']] += sale['quantity']
        elif prev_30_days <= date_obj < last_30_days:
            previous_sales[sale['coffee']] += sale['quantity']

declines = {}
for coffee in coffee_list:
    prev = previous_sales[coffee]
    recent = recent_sales[coffee]
    if prev > 0:
        change = ((recent - prev) / prev) * 100
        declines[coffee] = change

if declines:
    product_name, decline_percentage = min(declines.items(), key=lambda x: x[1])
    if decline_percentage < 0:
        st.error(f"⚠️ Son 30 gün içerisinde **{product_name}** satışları %{abs(decline_percentage):.1f} azaldı!!!")
    else:
        st.success(f"🎉 Son 30 gün içerisinde **{product_name}** satışları %{decline_percentage:.1f} arttı!!!")
else:
    st.info("Yeterli veri bulunamadı.")
