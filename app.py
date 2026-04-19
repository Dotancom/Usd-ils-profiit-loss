import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import altair as alt

# השינוי כאן: layout="centered" במקום "wide"
st.set_page_config(page_title="מכונת זמן - שער הדולר", layout="centered")

st.title("⏱️ מכונת זמן - השוואת שער דולר היסטורי")

# יצירת אזורי תצוגה
top_container = st.container()
st.divider()
chart_container = st.container()
st.divider()
bottom_container = st.container()

current_fx = 0.0
historical_fx = 0.0
display_label = ""
usd_input = 10000.0

# --- אזור הבקרות (תחתית המסך) ---
with bottom_container:
    st.subheader("⚙️ הגדרות וסימולציה")
    
    col_base1, col_base2 = st.columns(2)
    with col_base1:
        usd_input = st.number_input("סכום בדולרים ($)", value=10000.0, step=100.0, format="%.2f")
    with col_base2:
        mode = st.radio("מקור נתונים:", ("אוטומטי (מהבורסה)", "ידני (הקלדה)"), horizontal=True)

    if mode == "אוטומטי (מהבורסה)":
        today = datetime.date.today()
        sel_date = st.date_input("בחר תאריך היסטורי להשוואה", value=today - datetime.timedelta(days=365), max_value=today)
        display_label = sel_date.strftime('%d/%m/%Y')
        
        @st.cache_data(ttl=300)
        def get_data(d_obj):
            t = yf.Ticker("ILS=X")
            c = t.history(period="1d").Close.tolist().pop()
            s = d_obj - datetime.timedelta(days=7)
            h = t.history(start=s, end=d_obj + datetime.timedelta(days=1)).Close.tolist().pop()
            return c, h

        with st.spinner("מושך נתונים..."):
            try:
                current_fx, historical_fx = get_data(sel_date)
            except Exception as e:
                st.error("בעיה בחיבור לבורסה. ודא חיבור לאינטרנט.")
    else:
        c1, c2 = st.columns(2)
        current_fx = c1.number_input("שער דולר נוכחי", value=3.7000, format="%.4f")
        historical_fx = c2.number_input("שער היסטורי", value=3.6000, format="%.4f")
        display_label = "הזנה ידנית"

# --- אזור התוצאות (ראש המסך) והגרף ---
if current_fx > 0 and historical_fx > 0:
    val_now = usd_input * current_fx
    val_then = usd_input * historical_fx
    diff = val_now - val_then
    pct = ((current_fx / historical_fx) - 1) * 100

    with top_container:
        st.subheader(f"💵 ניתוח השווי עבור $ {usd_input:,.2f}")
        
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            st.info(f"₪ שער דולר נוכחי: {current_fx:.4f}")
        with c_info2:
            st.info(f"₪ שער היסטורי ({display_label}): {historical_fx:.4f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### השוואת שווי בשקלים")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("שווי נוכחי (היום)", f"₪ {val_now:,.2f}")
        m2.metric("שווי היסטורי (בעבר)", f"₪ {val_then:,.2f}")
        color = "normal" if diff >= 0 else "inverse"
        m3.metric("הפרש / רווח מטבע", f"₪ {diff:,.2f}", f"{pct:.2f}%", delta_color=color)

    # --- יצירת הגרף ---
    with chart_container:
        chart_data = pd.DataFrame({
            "תקופה": (f"שווי היסטורי (בעבר)", "שווי נוכחי (היום)"),
            "שווי": (val_then, val_now)
        })
        
        color_scale = alt.Scale(domain=(f"שווי היסטורי (בעבר)", "שווי נוכחי (היום)"), range=('#A0AEC0', '#2E8B57'))
        
        bars = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=80).encode(
            x=alt.X('תקופה:N', sort=None, axis=alt.Axis(title="", labelAngle=0, labelFontSize=14)),
            y=alt.Y('שווי:Q', axis=None),
            color=alt.Color('תקופה:N', scale=color_scale, legend=None)
        )
        
        text = bars.mark_text(align='center', baseline='bottom', dy=-10, fontSize=16, fontWeight='bold').encode(
            text=alt.Text('שווי:Q', format=',.0f')
        )
        
        final_chart = (bars + text).properties(height=350)
        
        # הדפסת הגרף ישירות ללא טריקים של עמודות רווח, כי כל המסך כבר ממורכז
        st.altair_chart(final_chart, use_container_width=True)