"""
CRM Dashboard - Olist Brazilian E-Commerce
Jalankan : streamlit run app.py
Data     : taruh CSV Olist di folder ./data
           (untuk peta, butuh juga olist_geolocation_dataset.csv)
Tema     : .streamlit/config.toml (base = "light") ikut disalin bersama file ini
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="CRM Dashboard",
    page_icon="✿",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA = Path(__file__).parent / "data"

# Streamlit >= 1.50 memakai width="stretch" (use_container_width sudah deprecated)
NEW_ST = tuple(int(x) for x in st.__version__.split(".")[:2]) >= (1, 50)

# ---------------------------------------------------------------------
# PALET WARNA
# ---------------------------------------------------------------------
GOLD = "#D97706"
BAMBOO = "#059669"
CYPRESS = "#2563EB"
CHRYSANTHEMUM = "#DC2626"
WILD_BERRY = "#1E3A8A"
VIOLET = "#7C3AED"
SLATE = "#64748B"

TEXT = "#1F2937"
MUTED = "#6B7280"
BORDER = "#E5E7EB"
BG = "#F8FAFC"
FONT = "Inter, 'Segoe UI', Arial, sans-serif"

SEGMENT_ORDER = [
    "Champions",
    "Loyal",
    "At Risk (high value)",
    "New / Promising",
    "Need Attention",
    "Hibernating",
]
SEGMENT_COLORS = {
    "Champions": BAMBOO,
    "Loyal": CYPRESS,
    "At Risk (high value)": CHRYSANTHEMUM,
    "New / Promising": GOLD,
    "Need Attention": VIOLET,
    "Hibernating": SLATE,
}
STRATEGY = {
    "Champions": "Program VIP / early access produk baru, minta review dan referral.",
    "Loyal": "Poin loyalitas, bundling, dan cross-selling produk komplementer.",
    "At Risk (high value)": "Kampanye win-back personal: voucher eksklusif dan pengingat via email.",
    "New / Promising": "Welcome series dan diskon pembelian kedua untuk mendorong repeat order.",
    "Need Attention": "Rekomendasi produk berdasarkan riwayat dan promo berbatas waktu.",
    "Hibernating": "Reaktivasi berbiaya rendah melalui email atau free shipping.",
}
REVIEW_COLORS = {
    "1": CHRYSANTHEMUM,
    "2": "#EA580C",
    "3": GOLD,
    "4": CYPRESS,
    "5": BAMBOO,
}

PAGES = [
    "1. Performa Bisnis",
    "2. Sebaran Pelanggan dan Konsentrasi Wilayah",
    "3. Analisis Nilai Pelanggan",
    "4. Distribusi, Kontribusi Revenue dan Pelanggan Terbaik",
    "5. Churn dan Loyalitas",
    "6. Analisis Pelanggan Berisiko, Retensi dan Kepuasan",
    "7. Strategi Pemasaran",
]
PAGE_SUBTITLE = {
    PAGES[0]: "Ringkasan performa penjualan dan komposisi pelanggan Olist Brazilian E-Commerce.",
    PAGES[1]: "Dari mana pelanggan berasal dan wilayah dengan kontribusi terbesar.",
    PAGES[2]: "Berapa nilai transaksi setiap pelanggan pada periode terpilih.",
    PAGES[3]: "Siapa pelanggan terbaik dan segmen mana yang menyumbang revenue terbesar.",
    PAGES[4]: "Pelanggan mana yang berpotensi tidak aktif dan seberapa loyal pelanggan saat ini.",
    PAGES[5]: "Prioritas win-back, retensi, dan kepuasan pelanggan.",
    PAGES[6]: "Strategi pemasaran yang harus diterapkan untuk setiap segmen pelanggan.",
}


# ---------------------------------------------------------------------
# HELPER HTML
# Markdown menganggap baris yang menjorok >= 4 spasi sebagai blok kode dan
# baris kosong memutus blok HTML. Karena itu HTML dipadatkan dulu.
# ---------------------------------------------------------------------
def html(markup: str) -> None:
    compact = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(compact, unsafe_allow_html=True)


# ---------------------------------------------------------------------
# STYLE GLOBAL
# ---------------------------------------------------------------------
html(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root, .stApp {{ color-scheme: light; }}

    html, body, .stApp {{
        font-family: {FONT};
    }}
    .stApp {{
        background: {BG};
        color: {TEXT};
    }}
    [data-testid="stHeader"] {{ background: transparent; }}

    /* --- Teks umum: paksa gelap agar tidak hilang di tema gelap --- */
    .stApp p, .stApp li, .stApp span, .stApp label,
    [data-testid="stMarkdownContainer"] {{
        color: {TEXT};
    }}
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {{
        color: {MUTED} !important;
        -webkit-text-fill-color: {MUTED} !important;
    }}

    /* --- Label widget (semua area) --- */
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] *,
    .stApp label {{
        color: {TEXT} !important;
        -webkit-text-fill-color: {TEXT} !important;
        opacity: 1 !important;
        font-size: 0.8rem;
        font-weight: 500;
    }}

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {{
        background: #FFFFFF;
        border-right: 1px solid {BORDER};
    }}

    /* --- Radio: semua teks pilihan gelap (sidebar DAN area utama) --- */
    [role="radiogroup"] label,
    [role="radiogroup"] label *,
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label * {{
        color: {TEXT} !important;
        -webkit-text-fill-color: {TEXT} !important;
        opacity: 1 !important;
        font-size: 0.86rem;
    }}

    /* Menu navigasi sidebar: tanpa titik radio, gaya daftar */
    [data-testid="stSidebar"] [role="radiogroup"] {{
        gap: 2px;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label {{
        padding: 0.45rem 0.7rem;
        border-radius: 8px;
        width: 100%;
        cursor: pointer;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{
        display: none;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        background: #F1F5F9;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
        background: #EEF3FE;
    }}

    /* Radio area utama (Tingkat wilayah, Ukuran titik): gaya pil */
    [data-testid="stMain"] [role="radiogroup"] {{
        gap: 6px;
    }}
    [data-testid="stMain"] [role="radiogroup"] label {{
        background: #FFFFFF;
        border: 1px solid {BORDER};
        border-radius: 999px;
        padding: 0.25rem 0.85rem;
        margin: 0;
        cursor: pointer;
    }}
    [data-testid="stMain"] [role="radiogroup"] label > div:first-child {{
        display: none;
    }}
    [data-testid="stMain"] [role="radiogroup"] label:hover {{
        border-color: {CYPRESS};
    }}
    [data-testid="stMain"] [role="radiogroup"] label:has(input:checked) {{
        background: #EEF3FE;
        border-color: {CYPRESS};
    }}

    /* Pilihan terpilih berwarna biru */
    [role="radiogroup"] label:has(input:checked),
    [role="radiogroup"] label:has(input:checked) * {{
        color: {CYPRESS} !important;
        -webkit-text-fill-color: {CYPRESS} !important;
        font-weight: 600;
    }}

    /* --- Input, dropdown, tag --- */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"] {{
        background: #FFFFFF !important;
        border-color: {BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT} !important;
    }}
    [data-baseweb="select"] *, [data-baseweb="input"] input,
    [data-baseweb="base-input"] input {{
        color: {TEXT} !important;
        -webkit-text-fill-color: {TEXT} !important;
    }}
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="base-input"] input::placeholder {{
        color: {MUTED} !important;
        -webkit-text-fill-color: {MUTED} !important;
    }}
    [data-baseweb="popover"] [role="listbox"],
    [data-baseweb="popover"] ul,
    [data-baseweb="calendar"] {{
        background: #FFFFFF !important;
    }}
    [data-baseweb="popover"] li, [data-baseweb="popover"] li *,
    [data-baseweb="calendar"] * {{
        color: {TEXT} !important;
    }}
    [data-baseweb="tag"] {{
        background: #EEF3FE !important;
    }}
    [data-baseweb="tag"] span, [data-baseweb="tag"] svg {{
        color: {CYPRESS} !important;
        fill: {CYPRESS} !important;
    }}

    /* --- Slider --- */
    [data-testid="stSlider"] [data-testid="stTickBarMin"],
    [data-testid="stSlider"] [data-testid="stTickBarMax"],
    [data-testid="stSlider"] [data-testid="stThumbValue"] {{
        color: {TEXT} !important;
    }}

    /* --- Alert (st.info / st.warning / st.error) --- */
    [data-testid="stAlert"] *,
    [data-testid="stAlertContainer"] * {{
        color: {TEXT} !important;
    }}

    /* --- Layout --- */
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}
    div.stButton > button, div.stDownloadButton > button {{
        border-radius: 8px;
        border: 1px solid {BORDER};
        background: #FFFFFF;
        color: {TEXT};
        font-weight: 500;
    }}
    div.stButton > button *, div.stDownloadButton > button * {{
        color: {TEXT} !important;
    }}
    div.stButton > button:hover, div.stDownloadButton > button:hover {{
        border-color: {CYPRESS};
    }}
    div.stButton > button:hover *, div.stDownloadButton > button:hover * {{
        color: {CYPRESS} !important;
    }}
    hr {{ border-color: {BORDER}; }}

    /* --- Komponen custom --- */
    .brand {{ display:flex; align-items:center; gap:.6rem; padding-bottom:1rem; }}
    .brand-mark {{
        width:34px; height:34px; display:flex; align-items:center; justify-content:center;
        border-radius:8px; background:{CYPRESS}; color:#fff; font-size:1.1rem; font-weight:700;
    }}
    .brand-name {{ color:{TEXT}; font-size:.95rem; font-weight:700; line-height:1.1; }}
    .brand-sub {{ color:{MUTED}; font-size:.7rem; margin-top:.15rem; }}
    .side-label {{
        color:{MUTED}; font-size:.7rem; font-weight:600; margin:.8rem 0 .3rem .1rem;
    }}
    .page-heading {{
        display:flex; align-items:flex-start; justify-content:space-between;
        gap:1rem; margin-bottom:1rem;
    }}
    .page-title {{ color:{TEXT}; font-size:1.65rem; font-weight:700; line-height:1.25; }}
    .page-subtitle {{ color:{MUTED}; font-size:.88rem; margin-top:.2rem; }}
    .date-chip {{ color:{MUTED}; font-size:.78rem; white-space:nowrap; padding-top:.4rem; }}
    .section-heading {{ margin:.3rem 0 .5rem 0; }}
    .section-title {{ color:{TEXT}; font-size:1rem; font-weight:700; }}
    .section-sub {{ color:{MUTED}; font-size:.76rem; margin-top:.15rem; }}
    .insight-card {{
        background:#fff; border:1px solid {BORDER}; border-radius:12px;
        padding:1rem; margin-bottom:.75rem;
    }}
    .insight-title {{ color:{TEXT}; font-size:.92rem; font-weight:600; margin-bottom:.25rem; }}
    .insight-copy {{ color:{MUTED}; font-size:.82rem; line-height:1.55; }}

    @media (max-width: 900px) {{
        .block-container {{ padding: 1rem 1rem 2rem 1rem; }}
        .page-title {{ font-size: 1.35rem; }}
        .date-chip {{ display: none; }}
    }}
    </style>
    """
)


# ---------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------
@st.cache_data(show_spinner="Memuat data Olist...")
def load_data() -> pd.DataFrame:
    cust = pd.read_csv(DATA / "olist_customers_dataset.csv")
    orders = pd.read_csv(
        DATA / "olist_orders_dataset.csv",
        parse_dates=["order_purchase_timestamp"],
    )
    pay = pd.read_csv(DATA / "olist_order_payments_dataset.csv")
    rev = pd.read_csv(DATA / "olist_order_reviews_dataset.csv")

    orders = orders[orders["order_status"] == "delivered"].copy()

    pay_total = pay.groupby("order_id", as_index=False)["payment_value"].sum()
    pay_type = (
        pay.sort_values("payment_value")
        .drop_duplicates("order_id", keep="last")[["order_id", "payment_type"]]
    )
    rev_avg = rev.groupby("order_id", as_index=False)["review_score"].mean()

    df = (
        orders.merge(cust, on="customer_id")
        .merge(pay_total, on="order_id")
        .merge(pay_type, on="order_id", how="left")
        .merge(rev_avg, on="order_id", how="left")
    )
    df["customer_city"] = df["customer_city"].str.title()

    return df[
        [
            "order_id",
            "customer_unique_id",
            "order_purchase_timestamp",
            "customer_state",
            "customer_city",
            "customer_zip_code_prefix",
            "payment_value",
            "payment_type",
            "review_score",
        ]
    ]


def load_geo():
    """Koordinat median per prefix kode pos. None jika file tidak ada.
    Pengecekan file dilakukan DI LUAR cache, supaya hasil None (file belum
    ada saat pertama dijalankan) tidak ikut tersimpan di cache."""
    path = DATA / "olist_geolocation_dataset.csv"
    if not path.exists():
        return None
    return _read_geo(str(path))


@st.cache_data(show_spinner="Memuat data lokasi...")
def _read_geo(path: str) -> pd.DataFrame:
    geo = pd.read_csv(
        path,
        usecols=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
    )
    # Buang titik di luar wilayah Brasil (ada outlier di dataset)
    geo = geo[
        geo["geolocation_lat"].between(-34, 6)
        & geo["geolocation_lng"].between(-74, -34)
    ]
    return geo.groupby("geolocation_zip_code_prefix", as_index=False).agg(
        lat=("geolocation_lat", "median"),
        lng=("geolocation_lng", "median"),
    ).rename(columns={"geolocation_zip_code_prefix": "zip_prefix"})


def build_rfm(frame: pd.DataFrame) -> pd.DataFrame:
    # Dataset Olist berakhir 2018, jadi tanggal acuan = transaksi terakhir.
    reference_date = frame["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    result = (
        frame.groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("payment_value", "sum"),
            avg_review=("review_score", "mean"),
            state=("customer_state", "last"),
            city=("customer_city", "last"),
            zip_prefix=("customer_zip_code_prefix", "last"),
        )
        .reset_index()
    )

    result["recency"] = (reference_date - result["last_purchase"]).dt.days
    result["R"] = pd.qcut(
        result["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    result["F"] = result["frequency"].clip(upper=5)
    result["M"] = pd.qcut(
        result["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    conditions = [
        (result["F"] >= 2) & (result["M"] >= 4) & (result["R"] >= 3),
        result["F"] >= 2,
        (result["R"] <= 2) & (result["M"] >= 4),
        (result["R"] >= 4) & (result["M"] < 4),
        (result["R"] <= 2) & (result["M"] < 4),
    ]
    result["segment"] = np.select(
        conditions,
        ["Champions", "Loyal", "At Risk (high value)", "New / Promising", "Hibernating"],
        default="Need Attention",
    )
    return result


# ---------------------------------------------------------------------
# HELPER TAMPILAN
# ---------------------------------------------------------------------
def rp(value: float) -> str:
    return f"R$ {value:,.0f}"


def show_chart(fig) -> None:
    # theme=None: pakai styling sendiri, bukan tema Streamlit yang mengganti
    # warna font (penyebab teks chart "hilang" saat tema gelap).
    if NEW_ST:
        st.plotly_chart(fig, width="stretch", theme=None)
    else:
        st.plotly_chart(fig, use_container_width=True, theme=None)


def show_table(data: pd.DataFrame, height=None) -> None:
    config = {}
    for column in ["Total Belanja", "Total Revenue", "Rata-rata Belanja"]:
        if column in data.columns:
            config[column] = st.column_config.NumberColumn(format="R$ %.0f")
    for column in ["Jumlah Pelanggan", "Jumlah Pesanan", "Pesanan", "Recency (hari)"]:
        if column in data.columns:
            config[column] = st.column_config.NumberColumn(format="%d")
    if "Pembelian Terakhir" in data.columns:
        config["Pembelian Terakhir"] = st.column_config.DatetimeColumn(format="DD MMM YYYY")
    kwargs = dict(hide_index=True, height=height, column_config=config)
    if NEW_ST:
        st.dataframe(data, width="stretch", **kwargs)
    else:
        st.dataframe(data, use_container_width=True, **kwargs)


def style_fig(fig, height=320, legend=False, x_title=None, y_title=None):
    """Styling seragam. Judul sengaja dikosongkan: judul chart dipasang lewat
    section_title(). (title=dict(...) tanpa text membuat Plotly menampilkan
    kata 'undefined'.)"""
    fig.update_layout(
        template="plotly_white",
        title=dict(text=""),
        height=height,
        margin=dict(l=8, r=8, t=40 if legend else 10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT, size=12),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title=dict(text=""),
            font=dict(size=11, color=TEXT),
        ),
        hoverlabel=dict(bgcolor="white", font=dict(color=TEXT, size=12)),
    )
    axis_font = dict(color=MUTED, size=11)
    fig.update_xaxes(
        title=dict(text=x_title, font=dict(color=MUTED, size=11)) if x_title else dict(text=None),
        showgrid=False,
        zeroline=False,
        linecolor=BORDER,
        tickfont=axis_font,
    )
    fig.update_yaxes(
        title=dict(text=y_title, font=dict(color=MUTED, size=11)) if y_title else dict(text=None),
        showgrid=True,
        gridcolor="#EEF2F7",
        zeroline=False,
        linecolor="rgba(0,0,0,0)",
        tickfont=axis_font,
    )
    return fig


def round_bars(fig, radius=6):
    # marker_cornerradius butuh Plotly >= 5.24; abaikan jika versi lebih lama.
    try:
        fig.update_traces(marker_cornerradius=radius, selector=dict(type="bar"))
    except ValueError:
        pass
    return fig


def metric_card(label, value, note, accent):
    html(
        f"""
        <div style="background:#FFFFFF;border:1px solid {BORDER};border-radius:12px;
                    padding:1rem 1.05rem;min-height:116px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:.8rem;color:{MUTED};font-weight:600;">{label}</span>
                <span style="width:9px;height:9px;border-radius:50%;background:{accent};"></span>
            </div>
            <div style="font-size:1.55rem;font-weight:700;color:{TEXT};margin-top:.5rem;line-height:1.2;">
                {value}
            </div>
            <div style="font-size:.74rem;color:{MUTED};margin-top:.35rem;">{note}</div>
        </div>
        """
    )


def section_title(title, subtitle=None):
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    html(f'<div class="section-heading"><div class="section-title">{title}</div>{sub}</div>')


def strategy_card(record):
    color = SEGMENT_COLORS.get(record["segment"], CYPRESS)
    html(
        f"""
        <div style="background:#FFFFFF;border:1px solid {BORDER};border-left:5px solid {color};
                    border-radius:12px;padding:1.05rem 1.15rem;min-height:178px;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:.75rem;">
                <div style="font-size:1rem;font-weight:700;color:{color};">{record["segment"]}</div>
                <span style="background:#F1F5F9;color:{TEXT};padding:.2rem .6rem;border-radius:999px;
                             font-size:.7rem;font-weight:600;white-space:nowrap;">
                    {int(record["pelanggan"]):,} pelanggan
                </span>
            </div>
            <div style="font-size:.83rem;line-height:1.55;color:{TEXT};margin:.6rem 0 .8rem;">
                {record["strategi"]}
            </div>
            <div style="display:flex;gap:1.25rem;flex-wrap:wrap;font-size:.76rem;color:{MUTED};">
                <span>Revenue: <b style="color:{TEXT}">{rp(record["revenue"])}</b></span>
                <span>Rata-rata: <b style="color:{TEXT}">{rp(record["avg_belanja"])}</b></span>
            </div>
        </div>
        """
    )


def segment_pie(rfm_frame, height=330, hole=0.6):
    seg = rfm_frame["segment"].value_counts().rename_axis("segment").reset_index(name="jumlah")
    fig = px.pie(
        seg,
        names="segment",
        values="jumlah",
        hole=hole,
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        category_orders={"segment": SEGMENT_ORDER},
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont=dict(color="white", size=11),
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="%{label}<br>%{value:,} pelanggan (%{percent})<extra></extra>",
        sort=False,
    )
    return style_fig(fig, height, legend=True)


# Layer peta dasar untuk customer_map(). Style "carto-positron" bawaan Plotly
# tidak dipakai lagi: seluruh endpoint tile raster CARTO (yang ditunjuk oleh
# plotly.js, baik versi lama maupun baru) sudah pensiun dan hanya menyajikan
# tile kosong, sehingga peta tampil blank. Sebagai gantinya dipakai tile ESRI
# Light Gray Canvas: gratis, tanpa token, dan tetap abu-abu terang seperti
# positron.
BASEMAP_LAYER = {
    "below": "traces",
    "sourcetype": "raster",
    "sourceattribution": "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
    "source": [
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
    ],
}


def customer_map(rfm_frame, geo):
    """Peta bubble: ukuran dan warna = metrik terpilih."""
    c1, c2, c3, _ = st.columns([1, 1, 1.4, 0.6])
    with c1:
        level = st.radio(
            "Tingkat wilayah", ["Per state", "Per kota"],
            horizontal=True, key="map_level",
        )
    with c2:
        metric_label = st.radio(
            "Ukuran titik", ["Pelanggan", "Revenue"],
            horizontal=True, key="map_metric",
        )
    with c3:
        base_style = st.radio(
            "Gaya peta", ["Peta dasar", "Tanpa peta dasar"],
            horizontal=True, key="map_base",
        )
    metric = "pelanggan" if metric_label == "Pelanggan" else "revenue"

    pts = rfm_frame.merge(geo, on="zip_prefix", how="inner")
    if pts.empty:
        st.info("Tidak ada pelanggan yang koordinatnya bisa dipetakan pada filter ini.")
        return
    coverage = len(pts) / len(rfm_frame)

    keys = ["state"] if level == "Per state" else ["state", "city"]
    grouped = (
        pts.groupby(keys)
        .agg(
            pelanggan=("customer_unique_id", "count"),
            revenue=("monetary", "sum"),
            lat=("lat", "mean"),
            lng=("lng", "mean"),
        )
        .reset_index()
    )
    if level == "Per kota":
        grouped = grouped.nlargest(150, metric)
        grouped["label"] = grouped["city"] + ", " + grouped["state"]
    else:
        grouped["label"] = grouped["state"]

    kwargs = dict(
        data_frame=grouped,
        lat="lat",
        lon="lng",
        size=metric,
        color=metric,
        size_max=45 if level == "Per state" else 32,
        hover_name="label",
        hover_data={"pelanggan": ":,", "revenue": ":,.0f", "lat": False, "lng": False},
        color_continuous_scale=["#BFDBFE", CYPRESS, WILD_BERRY],
        zoom=3.1,
        center=dict(lat=-14.5, lon=-52),
    )
    if base_style == "Peta dasar":
        # Trace peta harus cocok dengan plotly.js yang dibundel frontend
        # Streamlit: Streamlit lama (plotly.js 2.x) hanya merender
        # *scattermapbox*, Streamlit baru (plotly.js 3.x) hanya merender
        # *scattermap*. Peta dasar dipasang sebagai layer raster di atas
        # style white-bg (style tanpa tile), bukan style bawaan yang
        # menunjuk ke tile CARTO yang sudah pensiun.
        prefer_maplibre = NEW_ST
        try:
            maker = px.scatter_map if prefer_maplibre else px.scatter_mapbox
        except AttributeError:  # Plotly terlalu tua/lama untuk pilihan utama
            maker = px.scatter_mapbox if prefer_maplibre else px.scatter_map
        prefix = "map" if maker is px.scatter_map else "mapbox"
        fig = maker(**kwargs)
        fig.update_layout(
            **{
                f"{prefix}_style": "white-bg",
                f"{prefix}_layers": [BASEMAP_LAYER],
            }
        )
    else:
        # Tanpa basemap: tidak butuh koneksi ke server tile sama sekali.
        plain = {
            k: v for k, v in kwargs.items()
            if k not in ("lat", "lon", "zoom", "center")
        }
        fig = px.scatter(x="lng", y="lat", **plain)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
        fig.update_layout(plot_bgcolor="#F1F5F9")

    fig.update_traces(marker=dict(opacity=0.75))
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT),
        coloraxis_colorbar=dict(
            title=dict(text=metric_label),
            thickness=12,
            len=0.6,
            tickformat="~s",
        ),
    )
    show_chart(fig)
    st.caption(
        f"{coverage:.0%} pelanggan terpetakan. Koordinat = median lokasi kode pos "
        "pelanggan, jadi posisi titik bersifat perkiraan."
    )


# ---------------------------------------------------------------------
# LOAD DATA + FILTER SIDEBAR
# ---------------------------------------------------------------------
try:
    df = load_data()
except FileNotFoundError as error:
    st.error(
        f"File dataset tidak ditemukan: {error.filename}. "
        "Pastikan seluruh CSV Olist berada di folder `data/`."
    )
    st.stop()

if df.empty:
    st.warning("Dataset tidak memiliki pesanan dengan status delivered.")
    st.stop()

with st.sidebar:
    html(
        """
        <div class="brand">
            <div class="brand-mark">✿</div>
            <div>
                <div class="brand-name">Olist CRM</div>
                <div class="brand-sub">Customer analytics</div>
            </div>
        </div>
        <div class="side-label">Menu</div>
        """
    )

    page = st.radio("Navigasi", PAGES, label_visibility="collapsed", key="nav")

    html('<div class="side-label">Filter data</div>')

    min_date = df["order_purchase_timestamp"].min().date()
    max_date = df["order_purchase_timestamp"].max().date()
    date_range = st.date_input(
        "Periode transaksi",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    states = st.multiselect(
        "State pelanggan",
        sorted(df["customer_state"].dropna().unique()),
        placeholder="Semua state",
    )
    top_cities = df["customer_city"].dropna().value_counts().head(30).index
    cities = st.multiselect(
        "Kota pelanggan", sorted(top_cities), placeholder="Semua kota"
    )
    payment_types = st.multiselect(
        "Metode pembayaran",
        sorted(df["payment_type"].dropna().unique()),
        placeholder="Semua metode",
    )
    churn_days = st.slider(
        "Batas tidak aktif (hari)", min_value=60, max_value=365, value=180, step=30
    )

filtered = df.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
    filtered = filtered[
        (filtered["order_purchase_timestamp"] >= start_date)
        & (filtered["order_purchase_timestamp"] < end_date)
    ]
if states:
    filtered = filtered[filtered["customer_state"].isin(states)]
if cities:
    filtered = filtered[filtered["customer_city"].isin(cities)]
if payment_types:
    filtered = filtered[filtered["payment_type"].isin(payment_types)]

if filtered.empty:
    st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
    st.stop()

rfm = build_rfm(filtered)

with st.sidebar:
    st.markdown("---")
    html('<div class="side-label">Slicer</div>')
    segments = st.multiselect(
        "Segmen pelanggan",
        [s for s in SEGMENT_ORDER if s in set(rfm["segment"])],
        placeholder="Semua segmen",
    )
    st.markdown("---")
    html(
        f"""
        <div style="background:{WILD_BERRY};border-radius:12px;padding:1rem;">
            <div style="color:#FFFFFF;font-size:.95rem;font-weight:700;margin-bottom:.35rem;">
                Kenali pelanggan lebih dekat
            </div>
            <div style="font-size:.75rem;line-height:1.5;color:#DBEAFE;">
                Gunakan segmentasi RFM untuk memahami perilaku dan menyusun strategi retensi.
            </div>
        </div>
        """
    )

if segments:
    rfm = rfm[rfm["segment"].isin(segments)]
    filtered = filtered[filtered["customer_unique_id"].isin(rfm["customer_unique_id"])]

if filtered.empty:
    st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
    st.stop()

period_label = (
    f"{filtered['order_purchase_timestamp'].min():%d %b %Y}"
    f" – {filtered['order_purchase_timestamp'].max():%d %b %Y}"
)


# ---------------------------------------------------------------------
# HEADER HALAMAN + KPI
# ---------------------------------------------------------------------
html(
    f"""
    <div class="page-heading">
        <div>
            <div class="page-title">{page}</div>
            <div class="page-subtitle">{PAGE_SUBTITLE.get(page, "")}</div>
        </div>
        <div class="date-chip">Periode: {period_label}</div>
    </div>
    """
)

total_customers = rfm["customer_unique_id"].nunique()
total_orders = filtered["order_id"].nunique()
total_revenue = filtered["payment_value"].sum()
repeat_rate = (rfm["frequency"] > 1).mean()
avg_order = filtered["payment_value"].mean()

kpi_cols = st.columns(4, gap="medium")
with kpi_cols[0]:
    metric_card("Total pelanggan", f"{total_customers:,}", "Pelanggan unik pada periode terpilih", CYPRESS)
with kpi_cols[1]:
    metric_card("Total pesanan", f"{total_orders:,}", "Pesanan dengan status delivered", BAMBOO)
with kpi_cols[2]:
    metric_card("Total revenue", rp(total_revenue), "Akumulasi nilai pembayaran", WILD_BERRY)
with kpi_cols[3]:
    metric_card("Repeat customer", f"{repeat_rate:.1%}", "Pelanggan dengan lebih dari satu pesanan", CHRYSANTHEMUM)

st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------
# 1. PERFORMA BISNIS
# ---------------------------------------------------------------------
if page == PAGES[0]:
    left, right = st.columns([1.85, 1], gap="medium")

    with left:
        section_title("Tren revenue bulanan", "Perkembangan nilai transaksi dari waktu ke waktu")
        monthly = (
            filtered.set_index("order_purchase_timestamp")["payment_value"]
            .resample("MS")
            .sum()
            .reset_index()
        )
        fig = px.bar(
            monthly,
            x="order_purchase_timestamp",
            y="payment_value",
            color_discrete_sequence=[CYPRESS],
        )
        fig.update_traces(
            marker_line_width=0,
            hovertemplate="%{x|%b %Y}<br>Revenue: R$ %{y:,.0f}<extra></extra>",
        )
        round_bars(fig, 5)
        fig = style_fig(fig, 330)
        fig.update_xaxes(tickformat="%b %Y")
        fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
        show_chart(fig)

    with right:
        section_title("Distribusi segmen RFM", "Komposisi pelanggan berdasarkan perilaku")
        fig = segment_pie(rfm, 330)
        fig.update_layout(
            annotations=[
                dict(
                    text=f"<b>{total_customers:,}</b><br>pelanggan",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=15, color=TEXT),
                )
            ]
        )
        show_chart(fig)

    lower_left, lower_right = st.columns([1, 1.4], gap="medium")

    with lower_left:
        section_title("Metode pembayaran", "Metode yang paling sering digunakan")
        payment = (
            filtered["payment_type"]
            .fillna("Tidak diketahui")
            .str.replace("_", " ")
            .str.title()
            .value_counts()
            .rename_axis("metode")
            .reset_index(name="jumlah")
        )
        fig = px.pie(
            payment,
            names="metode",
            values="jumlah",
            hole=0.55,
            color_discrete_sequence=[CYPRESS, BAMBOO, GOLD, CHRYSANTHEMUM, VIOLET],
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            textfont=dict(color="white", size=11),
            marker=dict(line=dict(color="white", width=2)),
        )
        show_chart(style_fig(fig, 300, legend=True))

    with lower_right:
        section_title("Ringkasan performa", "Indikator utama pada periode terpilih")
        summary_metrics = pd.DataFrame(
            {
                "Metrik": [
                    "Total pelanggan", "Total pesanan", "Total revenue",
                    "Rata-rata nilai pesanan", "Repeat customer",
                ],
                "Nilai": [
                    f"{total_customers:,}", f"{total_orders:,}", rp(total_revenue),
                    rp(avg_order), f"{repeat_rate:.1%}",
                ],
            }
        )
        show_table(summary_metrics)


# ---------------------------------------------------------------------
# 2. SEBARAN PELANGGAN DAN KONSENTRASI WILAYAH
# ---------------------------------------------------------------------
elif page == PAGES[1]:
    section_title("Peta sebaran pelanggan", "Ukuran dan warna titik mengikuti metrik yang dipilih")
    geo = load_geo()
    if geo is None:
        st.info(
            "Peta membutuhkan file `olist_geolocation_dataset.csv`. "
            "Letakkan di folder `data/` lalu muat ulang halaman."
        )
    else:
        customer_map(rfm, geo)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    by_state = (
        rfm.groupby("state")
        .agg(pelanggan=("customer_unique_id", "count"), revenue=("monetary", "sum"))
        .reset_index()
    )

    left, right = st.columns(2, gap="medium")
    with left:
        section_title("Pelanggan per state", "15 state dengan jumlah pelanggan terbanyak")
        data = by_state.nlargest(15, "pelanggan").sort_values("pelanggan")
        fig = px.bar(data, x="pelanggan", y="state", orientation="h", color_discrete_sequence=[CYPRESS])
        round_bars(fig)
        show_chart(style_fig(fig, 430))

    with right:
        section_title("Revenue per state", "15 state dengan kontribusi revenue terbesar")
        data = by_state.nlargest(15, "revenue").sort_values("revenue")
        fig = px.bar(data, x="revenue", y="state", orientation="h", color_discrete_sequence=[CHRYSANTHEMUM])
        round_bars(fig)
        fig = style_fig(fig, 430)
        fig.update_xaxes(tickprefix="R$ ", tickformat="~s")
        show_chart(fig)

    by_city = (
        rfm["city"].value_counts().head(10)
        .rename_axis("kota").reset_index(name="pelanggan")
        .sort_values("pelanggan")
    )
    section_title("10 kota dengan pelanggan terbanyak")
    fig = px.bar(by_city, x="pelanggan", y="kota", orientation="h", color_discrete_sequence=[BAMBOO])
    round_bars(fig)
    show_chart(style_fig(fig, 350))


# ---------------------------------------------------------------------
# 3. ANALISIS NILAI PELANGGAN
# ---------------------------------------------------------------------
elif page == PAGES[2]:
    cap = rfm["monetary"].quantile(0.99)

    section_title(
        "Distribusi nilai belanja pelanggan",
        "Sebaran total belanja per pelanggan (hingga persentil ke-99)",
    )
    fig = px.histogram(
        rfm[rfm["monetary"] <= cap], x="monetary", nbins=45,
        color_discrete_sequence=[CYPRESS],
    )
    fig.update_traces(marker_line_width=0)
    fig = style_fig(fig, 340, x_title="Total belanja (R$)", y_title="Jumlah pelanggan")
    fig.update_xaxes(tickprefix="R$ ", tickformat="~s")
    show_chart(fig)

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    section_title("Nilai transaksi per pelanggan", "Cari customer ID atau unduh data hasil filter")
    search_customer = st.text_input("Cari customer_unique_id", placeholder="Masukkan customer ID...")
    table = rfm[
        ["customer_unique_id", "city", "state", "frequency", "monetary", "last_purchase", "segment"]
    ].sort_values("monetary", ascending=False)
    if search_customer:
        table = table[table["customer_unique_id"].str.contains(search_customer, case=False, na=False)]

    display_table = table.copy()
    display_table.columns = [
        "Customer ID", "Kota", "State", "Jumlah Pesanan",
        "Total Belanja", "Pembelian Terakhir", "Segmen",
    ]
    show_table(display_table)
    st.download_button(
        "Unduh data pelanggan (CSV)",
        table.to_csv(index=False).encode("utf-8"),
        "nilai_pelanggan.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------
# 4. DISTRIBUSI, KONTRIBUSI REVENUE DAN PELANGGAN TERBAIK
# ---------------------------------------------------------------------
elif page == PAGES[3]:
    left, right = st.columns([1, 1.7], gap="medium")

    with left:
        section_title("Komposisi segmen RFM", "Jumlah pelanggan per segmen")
        show_chart(segment_pie(rfm, 350, hole=0.5))

    with right:
        section_title("Top 10 pelanggan", "Diurutkan berdasarkan total belanja")
        top = rfm.nlargest(10, "monetary")[
            ["customer_unique_id", "city", "state", "frequency", "monetary", "segment"]
        ].copy()
        top.columns = ["Customer ID", "Kota", "State", "Pesanan", "Total Belanja", "Segmen"]
        show_table(top, height=350)

    section_title("Kontribusi revenue per segmen", "Total belanja pelanggan pada tiap segmen RFM")
    revenue_segment = (
        rfm.groupby("segment", as_index=False)["monetary"].sum()
        .sort_values("monetary", ascending=False)
    )
    fig = px.bar(
        revenue_segment, x="segment", y="monetary", color="segment",
        color_discrete_map=SEGMENT_COLORS,
    )
    fig.update_traces(marker_line_width=0, showlegend=False)
    round_bars(fig)
    fig = style_fig(fig, 330)
    fig.update_yaxes(tickprefix="R$ ", tickformat="~s")
    show_chart(fig)


# ---------------------------------------------------------------------
# 5. CHURN DAN LOYALITAS
# ---------------------------------------------------------------------
elif page == PAGES[4]:
    risk = rfm[rfm["recency"] > churn_days].copy()
    risk_revenue = risk["monetary"].sum()
    risk_share = len(risk) / max(len(rfm), 1)

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        metric_card("Pelanggan tidak aktif", f"{len(risk):,}", f"Lebih dari {churn_days} hari", CHRYSANTHEMUM)
    with c2:
        metric_card("Proporsi pelanggan", f"{risk_share:.1%}", "Dari seluruh pelanggan terfilter", BAMBOO)
    with c3:
        metric_card("Revenue historis", rp(risk_revenue), "Total belanja kelompok tidak aktif", WILD_BERRY)

    st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1], gap="medium")
    with left:
        section_title("Sebaran recency", "Jumlah hari sejak pembelian terakhir")
        fig = px.histogram(rfm, x="recency", nbins=40, color_discrete_sequence=[CYPRESS])
        fig.update_traces(marker_line_width=0)
        fig.add_vline(x=churn_days, line_dash="dash", line_color=CHRYSANTHEMUM, line_width=2)
        show_chart(style_fig(fig, 350, x_title="Hari sejak pembelian terakhir", y_title="Jumlah pelanggan"))

    with right:
        section_title("Frekuensi pembelian", "Berapa kali pelanggan melakukan transaksi")
        labels = ["1 kali", "2 kali", "3 kali", "4 kali atau lebih"]
        freq = rfm["frequency"].clip(upper=4).map(dict(zip([1, 2, 3, 4], labels)))
        freq_data = (
            freq.value_counts().reindex(labels, fill_value=0)
            .rename_axis("frekuensi").reset_index(name="pelanggan")
        )
        fig = px.bar(
            freq_data, x="frekuensi", y="pelanggan", color="frekuensi",
            color_discrete_sequence=[CYPRESS, BAMBOO, GOLD, WILD_BERRY],
        )
        fig.update_traces(showlegend=False)
        round_bars(fig)
        show_chart(style_fig(fig, 350))

    repeat_by_state = (
        rfm.assign(repeat=rfm["frequency"] > 1)
        .groupby("state")["repeat"].mean().mul(100).round(2)
        .reset_index(name="repeat_rate")
        .sort_values("repeat_rate", ascending=False)
    )
    section_title("Repeat rate per state", "Persentase pelanggan yang melakukan pembelian berulang")
    fig = px.bar(repeat_by_state, x="state", y="repeat_rate", color_discrete_sequence=[BAMBOO])
    round_bars(fig, 5)
    show_chart(style_fig(fig, 320, y_title="Repeat rate (%)"))


# ---------------------------------------------------------------------
# 6. PELANGGAN BERISIKO, RETENSI DAN KEPUASAN
# ---------------------------------------------------------------------
elif page == PAGES[5]:
    risk = rfm[rfm["recency"] > churn_days].copy()
    scores = filtered["review_score"].dropna()
    avg_review = scores.mean() if len(scores) else 0
    positive_review = (scores >= 4).mean() if len(scores) else 0

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        metric_card("Rata-rata skor review", f"{avg_review:.2f}", "Skala 1-5 dari pelanggan", CYPRESS)
    with c2:
        metric_card("Review positif", f"{positive_review:.1%}", "Skor 4 atau 5", BAMBOO)
    with c3:
        metric_card("Pelanggan prioritas", f"{len(risk):,}", "Kandidat win-back", CHRYSANTHEMUM)

    st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1], gap="medium")

    with left:
        section_title("Distribusi skor review", "Penilaian pelanggan setelah transaksi")
        review = (
            scores.round().astype(int).astype(str)
            .value_counts().sort_index()
            .rename_axis("skor").reset_index(name="jumlah")
        )
        fig = px.bar(
            review, x="skor", y="jumlah", color="skor",
            color_discrete_map=REVIEW_COLORS,
        )
        fig.update_traces(showlegend=False)
        round_bars(fig)
        show_chart(style_fig(fig, 340, x_title="Skor review"))

    with right:
        section_title("Fokus tindak lanjut", "Prioritas pelanggan berdasarkan nilai belanja")
        html(
            f"""
            <div class="insight-card">
                <div class="insight-title">Win-back campaign</div>
                <div class="insight-copy">
                    Ada <b style="color:{TEXT}">{len(risk):,} pelanggan</b> yang tidak
                    membeli lebih dari {churn_days} hari. Prioritaskan yang nilai belanja
                    historisnya tinggi untuk kampanye personal.
                </div>
            </div>
            <div class="insight-card">
                <div class="insight-title">Rekomendasi pendekatan</div>
                <div class="insight-copy">
                    Berikan voucher eksklusif, pengingat lewat email, atau gratis ongkir
                    untuk mendorong pelanggan kembali bertransaksi.
                </div>
            </div>
            """
        )

    section_title("Prioritas win-back", "50 pelanggan tidak aktif dengan nilai belanja tertinggi")
    risk_table = risk.nlargest(50, "monetary")[
        ["customer_unique_id", "city", "state", "recency", "frequency", "monetary", "segment"]
    ].copy()
    risk_table.columns = [
        "Customer ID", "Kota", "State", "Recency (hari)",
        "Jumlah Pesanan", "Total Belanja", "Segmen",
    ]
    show_table(risk_table)


# ---------------------------------------------------------------------
# 7. STRATEGI PEMASARAN
# ---------------------------------------------------------------------
elif page == PAGES[6]:
    section_title("Rekomendasi strategi per segmen", "Strategi retensi berdasarkan hasil segmentasi RFM")

    summary = (
        rfm.groupby("segment")
        .agg(
            pelanggan=("customer_unique_id", "count"),
            revenue=("monetary", "sum"),
            avg_belanja=("monetary", "mean"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    summary["strategi"] = summary["segment"].map(STRATEGY)

    records = summary.to_dict("records")
    for start in range(0, len(records), 3):
        cols = st.columns(3, gap="medium")
        for col, record in zip(cols, records[start:start + 3]):
            with col:
                strategy_card(record)

    section_title("Tabel ringkasan segmen", "Pelanggan, revenue, dan rekomendasi tindakan per segmen")
    table = summary[["segment", "pelanggan", "revenue", "avg_belanja", "strategi"]].copy()
    table.columns = ["Segmen", "Jumlah Pelanggan", "Total Revenue", "Rata-rata Belanja", "Strategi"]
    show_table(table)

    html(
        f"""
        <div style="background:#FFF7D6;border:1px solid #F1DE9A;border-left:5px solid {GOLD};
                    border-radius:10px;padding:1rem 1.1rem;margin-top:1rem;color:#4A4326;
                    font-size:.85rem;line-height:1.6;">
            <b style="color:#2E2A16;">Catatan:</b> pada filter saat ini hanya
            {repeat_rate:.1%} pelanggan yang membeli lebih dari sekali. Karena itu segmen
            Loyal relatif kecil dan strategi retensi difokuskan pada mendorong pembelian kedua.
        </div>
        """
    )


# ---------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------
st.markdown("---")
html(f'<div style="color:{MUTED};font-size:.74rem;">Olist CRM Dashboard · Customer Relationship Management</div>')