import streamlit as st
import yfinance as yf
import datetime
import pandas as pd

st.set_page_config(page_title="מכונת זמן - שער הדולר", layout="wide")
st.title("⏱️ מכונת זמן - השוואת שער דולר היסטורי")

st.sidebar.header("הגדרות בדיקה")
usd_amount = st.sidebar.number_input("סכום בדולרים ($)", value=10000.0, step=100.0, format="%.2f")

# בחירת מצב עבודה (מתג בין אוטומטי לידני)
st.sidebar.markdown("---")
input_mode = st.sidebar.radio("מקור הנתונים לשערים:", ("משיכה אוטומטית (זמן אמת)", "הזנה ידנית (סימולציה)"))
st.sidebar.markdown("---")

current_fx = None
historical_fx = None
display_date = "שער היסטורי"

# לוגיקה למצב אוטומטי
if input_mode == "משיכה אוטומטית (זמן אמת)":
    today = datetime.date.today()
    selected_date = st.sidebar.date_input("בחר תאריך היסטורי להשוואה", 
                                          value=today - datetime.timedelta(days=365), 
                                          max_value=today)
    display_date = selected_date.strftime('%d/%m/%Y')

    @st.cache_data(ttl=300) 
    def get_current_rate():
        ticker = yf.Ticker("ILS=X")
        data = ticker.history(period="1d")
        if data.empty:
            raise ValueError("Yahoo Finance החזיר טבלה ריקה לשער הנוכחי.")
        return data.Close.tolist().pop()

    @st.cache_data
    def get_historical_rate(date_obj):
        ticker = yf.Ticker("ILS=X")
        start_date = date_obj - datetime.timedelta(days=7)
        end_date = date_obj + datetime.timedelta(days=1)
        data = ticker.history(start=start_date, end=end_date)
        if data.empty:
             raise ValueError("לא נמצאו נתונים היסטוריים לתאריך המבוקש.")
        return data.Close.tolist().pop()

    with st.spinner("מושך שערי חליפין בזמן אמת מ-Yahoo Finance..."):
        try:
            current_fx = get_current_rate()
            historical_fx = get_historical_rate(selected_date)
        except Exception as e:
            st.error(f"אירעה שגיאה טכנית. פירוט השגיאה: {e}")
            st.stop()

# לוגיקה למצב ידני
else:
    current_fx = st.sidebar.number_input("שער דולר נוכחי (₪)", value=3.70, step=0.01)
    historical_fx = st.sidebar.number_input("שער דולר היסטורי (₪)", value=3.60, step=0.01)
    display_date = "הוזן ידנית"


# --- חישובים ותצוגת הדשבורד (רץ רק אם יש שערים) ---
if current_fx and historical_fx:
    current_value_ils = usd_amount * current_fx
    historical_value_ils = usd_amount * historical_fx
    
    diff_ils = current_value_ils - historical_value_ils
    pct_change = ((current_fx / historical_fx) - 1) * 100
    
    st.subheader(f"💵 ניתוח השווי עבור $ {usd_amount:,.2f}")
    
    col_fx_1, col_fx_2 = st.columns(2)
    with col_fx_1:
        st.info(f"**שער דולר נוכחי:** {current_fx:.4f} ₪")
    with col_fx_2:
        st.info(f"**שער היסטורי ({display_date}):** {historical_fx:.4f} ₪")
    
    st.markdown("### השוואת שווי בשקלים")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("שווי נוכחי (היום)", f"₪ {current_value_ils:,.2f}")
        
    with col2:
        st.metric("שווי היסטורי (בעבר)", f"₪ {historical_value_ils:,.2f}")
        
    with col3:
        delta_color = "normal" if diff_ils >= 0 else "inverse"
        st.metric("הפרש / רווח מטבע", f"₪ {diff_ils:,.2f}", f"{pct_change:.2f}%", delta_color=delta_color)
    
    st.divider()
    
    # בניית הגרף (עם סוגריים עגולים כדי למנוע באגים)
    chart_data = pd.DataFrame(
        {"שווי (₪)": (historical_value_ils, current_value_ils)}, 
        index=(f"בעבר ({display_date})", "היום")
    )
    st.bar_chart(chart_data, color="#2e7b54")