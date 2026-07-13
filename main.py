import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import time
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Finans Veri Ajanı", page_icon="📊", layout="wide")

# ============================================
# SESSION STATE - Takip Listesi & Ayarlar
# ============================================
def init_session_state():
    if "takip_listesi" not in st.session_state:
        st.session_state.takip_listesi = [
            {"sembol": "AAPL", "isim": "Apple", "tur": "Hisse (ABD)", "aktif": True},
            {"sembol": "THYAO.IS", "isim": "Türk Hava Yolları", "tur": "BIST 100", "aktif": True},
            {"sembol": "GARAN.IS", "isim": "Garanti BBVA", "tur": "BIST 100", "aktif": True},
            {"sembol": "BTC-USD", "isim": "Bitcoin", "tur": "Kripto", "aktif": True},
            {"sembol": "ETH-USD", "isim": "Ethereum", "tur": "Kripto", "aktif": True},
            {"sembol": "GC=F", "isim": "Altın", "tur": "Emtia", "aktif": True},
            {"sembol": "CL=F", "isim": "Ham Petrol", "tur": "Emtia", "aktif": True},
            {"sembol": "EURUSD=X", "isim": "EUR/USD", "tur": "Forex", "aktif": True},
            {"sembol": "USDTRY=X", "isim": "USD/TRY", "tur": "Forex", "aktif": True},
            {"sembol": "XU100.IS", "isim": "BIST 100 Endeks", "tur": "Endeks", "aktif": True},
        ]
    if "secili_sembol" not in st.session_state:
        st.session_state.secili_sembol = "AAPL"
    if "indikatorler" not in st.session_state:
        st.session_state.indikatorler = {
            "sma_20": {"aktif": True, "period": 20, "color": "#FFA500"},
            "sma_50": {"aktif": False, "period": 50, "color": "#00CED1"},
            "ema_12": {"aktif": False, "period": 12, "color": "#FF69B4"},
            "rsi": {"aktif": False, "period": 14, "color": "#9370DB"},
            "macd": {"aktif": False, "fast": 12, "slow": 26, "signal": 9},
            "bollinger": {"aktif": False, "period": 20, "std": 2, "color": "#20B2AA"},
        }
    if "zoom_aralik" not in st.session_state:
        st.session_state.zoom_aralik = None

init_session_state()

# ============================================
# VARLIK KÜTÜPHANESİ - Önerilen Varlıklar
# ============================================
VARLIK_KUTUPHANESI = {
    "BIST 100": [
        ("THYAO.IS", "Türk Hava Yolları"), ("GARAN.IS", "Garanti BBVA"), ("ASELS.IS", "Aselsan"),
        ("KCHOL.IS", "Koç Holding"), ("SISE.IS", "Şişecam"), ("BIMAS.IS", "BİM"),
        ("EREGL.IS", "Ereğli Demir Çelik"), ("TUPRS.IS", "Tüpraş"), ("SAHOL.IS", "Sabancı Holding"),
        ("AKBNK.IS", "Akbank"), ("YKBNK.IS", "Yapı Kredi"), ("ISCTR.IS", "İş Bankası"),
        ("KRDMD.IS", "Kardemir"), ("PETKM.IS", "Petkim"), ("TOASO.IS", "Tofaş"),
        ("ARCLK.IS", "Arçelik"), ("HEKTS.IS", "Hektaş"), ("KOZAA.IS", "Koza Altın"),
        ("PGSUS.IS", "Pegasus"), ("TCELL.IS", "Turkcell"),
    ],
    "Hisse (ABD)": [
        ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("GOOGL", "Alphabet"), ("AMZN", "Amazon"),
        ("TSLA", "Tesla"), ("META", "Meta"), ("NVDA", "NVIDIA"), ("NFLX", "Netflix"),
        ("AMD", "AMD"), ("INTC", "Intel"), ("IBM", "IBM"), ("DIS", "Disney"),
        ("BA", "Boeing"), ("JPM", "JPMorgan"), ("V", "Visa"), ("MA", "Mastercard"),
        ("WMT", "Walmart"), ("KO", "Coca-Cola"), ("PEP", "PepsiCo"), ("PFE", "Pfizer"),
    ],
    "Kripto": [
        ("BTC-USD", "Bitcoin"), ("ETH-USD", "Ethereum"), ("BNB-USD", "Binance Coin"),
        ("SOL-USD", "Solana"), ("XRP-USD", "Ripple"), ("ADA-USD", "Cardano"),
        ("DOGE-USD", "Dogecoin"), ("AVAX-USD", "Avalanche"), ("DOT-USD", "Polkadot"),
        ("MATIC-USD", "Polygon"), ("LINK-USD", "Chainlink"), ("LTC-USD", "Litecoin"),
    ],
    "Emtia": [
        ("GC=F", "Altın"), ("SI=F", "Gümüş"), ("CL=F", "Ham Petrol (WTI)"),
        ("BZ=F", "Brent Petrol"), ("NG=F", "Doğalgaz"), ("HG=F", "Bakır"),
        ("PL=F", "Platin"), ("PA=F", "Paladyum"), ("ZC=F", "Mısır"),
        ("ZW=F", "Buğday"), ("ZS=F", "Soya Fasulyesi"), ("KC=F", "Kahve"),
    ],
    "Forex": [
        ("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("USDJPY=X", "USD/JPY"),
        ("USDCHF=X", "USD/CHF"), ("AUDUSD=X", "AUD/USD"), ("USDCAD=X", "USD/CAD"),
        ("EURGBP=X", "EUR/GBP"), ("EURJPY=X", "EUR/JPY"), ("GBPJPY=X", "GBP/JPY"),
        ("USDTRY=X", "USD/TRY"), ("EURTRY=X", "EUR/TRY"), ("GBPTRY=X", "GBP/TRY"),
    ],
    "Endeks": [
        ("XU100.IS", "BIST 100"), ("^GSPC", "S&P 500"), ("^DJI", "Dow Jones"),
        ("^IXIC", "NASDAQ"), ("^FTSE", "FTSE 100"), ("^N225", "Nikkei 225"),
        ("^GDAXI", "DAX 40"), ("^FCHI", "CAC 40"), ("^HSI", "Hang Seng"),
    ],
}

# ============================================
# İNDİKATÖR FONKSİYONLARI
# ============================================
def sma(seri: pd.Series, period: int) -> pd.Series:
    return seri.rolling(window=period).mean()

def ema(seri: pd.Series, period: int) -> pd.Series:
    return seri.ewm(span=period, adjust=False).mean()

def rsi(seri: pd.Series, period: int = 14) -> pd.Series:
    delta = seri.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(seri: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(seri, fast) - ema(seri, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger(seri: pd.Series, period: int = 20, std_dev: int = 2):
    orta = sma(seri, period)
    std = seri.rolling(window=period).std()
    ust = orta + (std * std_dev)
    alt = orta - (std * std_dev)
    return ust, orta, alt

# ============================================
# VERİ KAYNAKLARI (Orijinal Kod Korundu)
# ============================================
@dataclass
class VeriPaketi:
    sembol: str
    kaynak: str
    zaman_dilimi: str
    veri: pd.DataFrame
    gecikme: str
    son_guncelleme: datetime

class VeriKaynagi(ABC):
    @abstractmethod
    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        pass

    @abstractmethod
    def destekler(self, sembol: str) -> bool:
        pass

class YahooFinanceKaynagi(VeriKaynagi):
    def __init__(self):
        self.isim = "Yahoo Finance"
        self.gecikme = "15dk gecikme (ABD), günlük (diğer)"

    def destekler(self, sembol: str) -> bool:
        return True

    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        interval_map = {"1d": "1d", "1h": "1h", "15m": "15m", "5m": "5m", "1m": "1m"}
        interval = interval_map.get(periyot, "1d")

        try:
            ticker = yf.Ticker(sembol)
            if periyot in ["1m", "5m", "15m"]:
                df = ticker.history(period="7d", interval=interval)
            else:
                df = ticker.history(period="6mo", interval=interval)

            if df.empty:
                raise ValueError("Veri bulunamadı")

            return VeriPaketi(
                sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                veri=df, gecikme="15dk gecikme", son_guncelleme=datetime.now()
            )
        except Exception as e:
            raise Exception(f"Yahoo Finance hatası: {e}")

class AlphaVantageKaynagi(VeriKaynagi):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.isim = "Alpha Vantage"
        self.gecikme = "15dk gecikme"
        self._son_cagri = 0

    def _rate_limit(self):
        gecen = time.time() - self._son_cagri
        if gecen < 12:
            time.sleep(12 - gecen)
        self._son_cagri = time.time()

    def destekler(self, sembol: str) -> bool:
        return True

    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        self._rate_limit()
        function_map = {"1d": "TIME_SERIES_DAILY", "1h": "TIME_SERIES_INTRADAY",
                        "15m": "TIME_SERIES_INTRADAY", "5m": "TIME_SERIES_INTRADAY", "1m": "TIME_SERIES_INTRADAY"}
        function = function_map.get(periyot, "TIME_SERIES_DAILY")

        params = {"function": function, "symbol": sembol, "apikey": self.api_key, "outputsize": "full"}
        if periyot != "1d":
            interval_map = {"1h": "60min", "15m": "15min", "5m": "5min", "1m": "1min"}
            params["interval"] = interval_map.get(periyot, "5min")

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            time_series_key = [k for k in data.keys() if "Time Series" in k][0]
            df_data = data[time_series_key]
            df = pd.DataFrame.from_dict(df_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float)

            return VeriPaketi(
                sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                veri=df, gecikme="15dk gecikme", son_guncelleme=datetime.now()
            )
        except Exception as e:
            raise Exception(f"Alpha Vantage hatası: {e}")

class TwelveDataKaynagi(VeriKaynagi):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.isim = "Twelve Data"
        self.gecikme = "Gerçek zamanlı (ücretli) / 15dk gecikme (ücretsiz)"

    def destekler(self, sembol: str) -> bool:
        return True

    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        interval_map = {"1d": "1day", "1h": "1h", "15m": "15min", "5m": "5min", "1m": "1min"}
        interval = interval_map.get(periyot, "1day")

        params = {"symbol": sembol, "interval": interval, "apikey": self.api_key, "outputsize": 5000}
        if baslangic: params["start_date"] = baslangic
        if bitis: params["end_date"] = bitis

        try:
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=10)
            data = response.json()
            if "values" not in data:
                raise ValueError(data.get("message", "Bilinmeyen hata"))

            df = pd.DataFrame(data["values"])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df = df.sort_index().astype(float)

            return VeriPaketi(
                sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                veri=df, gecikme="15dk gecikme (ücretsiz)", son_guncelleme=datetime.now()
            )
        except Exception as e:
            raise Exception(f"Twelve Data hatası: {e}")

class MockVeriKaynagi(VeriKaynagi):
    def __init__(self, seed: int = 42):
        self.isim = "Mock Veri"
        self.gecikme = "Gerçek zamanlı (simüle)"
        self.seed = seed

    def destekler(self, sembol: str) -> bool:
        return True

    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        np.random.seed(self.seed)

        if periyot == "1d":
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        elif periyot == "1h":
            dates = pd.date_range(end=datetime.now(), periods=7*24, freq='H')
        elif periyot == "15m":
            dates = pd.date_range(end=datetime.now(), periods=7*24*4, freq='15min')
        else:
            dates = pd.date_range(end=datetime.now(), periods=1000, freq='5min')

        fiyat = 100
        veriler = []
        for _ in dates:
            degisim = np.random.normal(0, 0.02)
            fiyat *= (1 + degisim)
            veriler.append({
                'Open': fiyat * (1 + np.random.normal(0, 0.005)),
                'High': fiyat * (1 + abs(np.random.normal(0, 0.01))),
                'Low': fiyat * (1 - abs(np.random.normal(0, 0.01))),
                'Close': fiyat,
                'Volume': int(np.random.uniform(100000, 1000000))
            })

        df = pd.DataFrame(veriler, index=dates)
        df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
        df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)

        return VeriPaketi(
            sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
            veri=df, gecikme="Simüle (test verisi)", son_guncelleme=datetime.now()
        )

class AkilliVeriKoordinatoru:
    def __init__(self):
        self.kaynaklar = []

    def kaynak_ekle(self, kaynak: VeriKaynagi, oncelik: int = 0):
        self.kaynaklar.append((oncelik, kaynak))
        self.kaynaklar.sort(key=lambda x: x[0])

    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        for oncelik, kaynak in self.kaynaklar:
            if not kaynak.destekler(sembol):
                continue
            try:
                return kaynak.veri_cek(sembol, periyot, baslangic, bitis)
            except Exception:
                continue
        raise Exception("Tüm veri kaynakları başarısız oldu!")

# ============================================
# ANLIK FİYAT ÇEKME
# ============================================
@st.cache_data(ttl=60)
def anlik_fiyat_cek(sembol: str) -> dict:
    """Sembolün anlık fiyat bilgilerini çeker."""
    try:
        ticker = yf.Ticker(sembol)
        info = ticker.info
        hist = ticker.history(period="2d")

        if hist.empty or len(hist) < 1:
            return {"hata": "Veri bulunamadı"}

        son_kapanis = hist['Close'].iloc[-1]
        onceki_kapanis = hist['Close'].iloc[-2] if len(hist) > 1 else son_kapanis
        degisim = son_kapanis - onceki_kapanis
        degisim_yuzde = (degisim / onceki_kapanis) * 100 if onceki_kapanis != 0 else 0

        return {
            "fiyat": son_kapanis,
            "degisim": degisim,
            "degisim_yuzde": degisim_yuzde,
            "hacim": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
            "yuksek": hist['High'].iloc[-1],
            "dusuk": hist['Low'].iloc[-1],
            "hata": None
        }
    except Exception as e:
        return {"hata": str(e)}

# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.title("📊 Çok Kaynaklı Finans Veri Ajanı")
    st.markdown("Yahoo Finance, Alpha Vantage, Twelve Data ve Mock veri kaynaklarını kullanır.")

    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.header("⚙️ Ayarlar")

        # --- API Anahtarları ---
        with st.expander("🔑 API Anahtarları", expanded=False):
            alpha_key = st.text_input("Alpha Vantage API Key", type="password")
            twelve_key = st.text_input("Twelve Data API Key", type="password")

        # --- Zaman Dilimi ---
        periyot = st.selectbox("Zaman Dilimi",
                              ["1d", "1h", "15m", "5m", "1m"],
                              format_func=lambda x: {"1d": "📅 Günlük", "1h": "🕐 Saatlik",
                                                     "15m": "⏱️ 15 Dakika", "5m": "⏱️ 5 Dakika", "1m": "⏱️ 1 Dakika"}[x])

        st.divider()

        # --- İNDİKATÖR AYARLARI ---
        st.subheader("📈 İndikatörler")

        ind_col1, ind_col2 = st.columns(2)

        with ind_col1:
            st.session_state.indikatorler["sma_20"]["aktif"] = st.checkbox(
                "SMA 20", value=st.session_state.indikatorler["sma_20"]["aktif"])
            st.session_state.indikatorler["sma_50"]["aktif"] = st.checkbox(
                "SMA 50", value=st.session_state.indikatorler["sma_50"]["aktif"])
            st.session_state.indikatorler["ema_12"]["aktif"] = st.checkbox(
                "EMA 12", value=st.session_state.indikatorler["ema_12"]["aktif"])

        with ind_col2:
            st.session_state.indikatorler["rsi"]["aktif"] = st.checkbox(
                "RSI", value=st.session_state.indikatorler["rsi"]["aktif"])
            st.session_state.indikatorler["macd"]["aktif"] = st.checkbox(
                "MACD", value=st.session_state.indikatorler["macd"]["aktif"])
            st.session_state.indikatorler["bollinger"]["aktif"] = st.checkbox(
                "Bollinger", value=st.session_state.indikatorler["bollinger"]["aktif"])

        st.divider()

        # --- TAKİP LİSTESİ YÖNETİMİ ---
        st.subheader("📋 Takip Listem")

        # Varlık Ekleme
        with st.expander("➕ Varlık Ekle", expanded=False):
            tur_secimi = st.selectbox("Kategori", list(VARLIK_KUTUPHANESI.keys()))
            varliklar = VARLIK_KUTUPHANESI[tur_secimi]
            varlik_secimi = st.selectbox("Varlık", varliklar, format_func=lambda x: f"{x[0]} - {x[1]}")

            if st.button("Listeye Ekle", use_container_width=True):
                mevcut_semboller = [v["sembol"] for v in st.session_state.takip_listesi]
                if varlik_secimi[0] not in mevcut_semboller:
                    st.session_state.takip_listesi.append({
                        "sembol": varlik_secimi[0],
                        "isim": varlik_secimi[1],
                        "tur": tur_secimi,
                        "aktif": True
                    })
                    st.success(f"✅ {varlik_secimi[1]} eklendi!")
                    st.rerun()
                else:
                    st.warning("⚠️ Bu varlık zaten listede!")

        # Listeyi Göster ve Yönet
        st.markdown("---")
        for i, varlik in enumerate(st.session_state.takip_listesi):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{varlik['sembol']}**  \n<small>{varlik['isim']} | {varlik['tur']}</small>",
                          unsafe_allow_html=True)
            with col_b:
                if st.button("🗑️", key=f"sil_{i}", help=f"{varlik['isim']} sil"):
                    st.session_state.takip_listesi.pop(i)
                    st.rerun()

        st.divider()
        use_mock = st.checkbox("🧪 Mock Veri Kullan (Test)", value=False)

    # ==================== ANA İÇERİK ====================

    # --- ANLIK FİYAT KARTLARI ---
    st.subheader("💰 Anlık Piyasa Verileri")

    aktif_varliklar = [v for v in st.session_state.takip_listesi if v.get("aktif", True)]

    if aktif_varliklar:
        # 4 sütunlu kart düzeni
        cols_per_row = 4
        rows = [aktif_varliklar[i:i+cols_per_row] for i in range(0, len(aktif_varliklar), cols_per_row)]

        for row in rows:
            cols = st.columns(len(row))
            for col, varlik in zip(cols, row):
                with col:
                    with st.spinner(f"⏳ {varlik['sembol']}..."):
                        veri = anlik_fiyat_cek(varlik["sembol"])

                    if veri.get("hata"):
                        st.error(f"❌ {varlik['sembol']}: {veri['hata']}")
                    else:
                        fiyat = veri["fiyat"]
                        degisim = veri["degisim"]
                        degisim_yuzde = veri["degisim_yuzde"]

                        renk = "🟢" if degisim >= 0 else "🔴"
                        isaret = "+" if degisim >= 0 else ""

                        st.metric(
                            label=f"{renk} {varlik['isim']} ({varlik['sembol']})",
                            value=f"{fiyat:,.4f}" if fiyat < 1 else f"{fiyat:,.2f}",
                            delta=f"{isaret}{degisim_yuzde:.2f}% ({isaret}{degisim:,.4f})" if fiyat < 1 else f"{isaret}{degisim_yuzde:.2f}% ({isaret}{degisim:,.2f})",
                            delta_color="normal"
                        )
                        st.caption(f"Hacim: {veri['hacim']:,} | Yüksek: {veri['yuksek']:.2f} | Düşük: {veri['dusuk']:.2f}")
    else:
        st.info("📭 Takip listeniz boş. Sidebar'dan varlık ekleyin.")

    st.divider()

    # --- GRAFİK BÖLÜMÜ ---
    st.subheader("📊 Detaylı Grafik")

    # Sembol seçimi (takip listesinden)
    secenekler = [(v["sembol"], f"{v['isim']} ({v['sembol']})") for v in st.session_state.takip_listesi]
    if secenekler:
        secili = st.selectbox("Grafik için sembol seç", secenekler, format_func=lambda x: x[1])
        secili_sembol = secili[0]
    else:
        secili_sembol = st.text_input("Sembol girin (örn: AAPL)", value="AAPL")

    if st.button("🚀 Grafiği Çiz", type="primary", use_container_width=True):
        with st.spinner("Veri çekiliyor..."):
            koordinator = AkilliVeriKoordinatoru()

            if twelve_key:
                koordinator.kaynak_ekle(TwelveDataKaynagi(twelve_key), 1)
            if alpha_key:
                koordinator.kaynak_ekle(AlphaVantageKaynagi(alpha_key), 2)

            koordinator.kaynak_ekle(YahooFinanceKaynagi(), 3)

            if use_mock:
                koordinator.kaynak_ekle(MockVeriKaynagi(), 99)

            try:
                paket = koordinator.veri_cek(secili_sembol, periyot)
                df = paket.veri

                # Bilgi satırı
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📡 Kaynak", paket.kaynak)
                col2.metric("⏱️ Gecikme", paket.gecikme)
                col3.metric("📊 Veri Sayısı", f"{len(df)} satır")
                col4.metric("💵 Son Kapanış", f"{df['Close'].iloc[-1]:.4f}" if df['Close'].iloc[-1] < 1 else f"{df['Close'].iloc[-1]:.2f}")

                st.success(f"✅ {paket.kaynak} üzerinden veri alındı!")

                # ==================== GRAFİK ÇİZİMİ (ZOOM + İNDİKATÖRLER) ====================

                # Alt grafik sayısını belirle
                alt_grafikler = []
                if st.session_state.indikatorler["rsi"]["aktif"]:
                    alt_grafikler.append("rsi")
                if st.session_state.indikatorler["macd"]["aktif"]:
                    alt_grafikler.append("macd")

                rows = 1 + len(alt_grafikler)
                row_heights = [0.6] + [0.2] * len(alt_grafikler)

                fig = make_subplots(
                    rows=rows, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=row_heights,
                    subplot_titles=[f"{secili_sembol} - {periyot}"] + alt_grafikler
                )

                # --- ANA GRAFİK: Candlestick ---
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=secili_sembol,
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ), row=1, col=1)

                # --- İNDİKATÖRLER ---
                close = df['Close']

                # SMA 20
                if st.session_state.indikatorler["sma_20"]["aktif"]:
                    sma20 = sma(close, st.session_state.indikatorler["sma_20"]["period"])
                    fig.add_trace(go.Scatter(
                        x=df.index, y=sma20,
                        mode='lines', name=f"SMA {st.session_state.indikatorler['sma_20']['period']}",
                        line=dict(color=st.session_state.indikatorler["sma_20"]["color"], width=1.5)
                    ), row=1, col=1)

                # SMA 50
                if st.session_state.indikatorler["sma_50"]["aktif"]:
                    sma50 = sma(close, st.session_state.indikatorler["sma_50"]["period"])
                    fig.add_trace(go.Scatter(
                        x=df.index, y=sma50,
                        mode='lines', name=f"SMA {st.session_state.indikatorler['sma_50']['period']}",
                        line=dict(color=st.session_state.indikatorler["sma_50"]["color"], width=1.5)
                    ), row=1, col=1)

                # EMA 12
                if st.session_state.indikatorler["ema_12"]["aktif"]:
                    ema12 = ema(close, st.session_state.indikatorler["ema_12"]["period"])
                    fig.add_trace(go.Scatter(
                        x=df.index, y=ema12,
                        mode='lines', name=f"EMA {st.session_state.indikatorler['ema_12']['period']}",
                        line=dict(color=st.session_state.indikatorler["ema_12"]["color"], width=1.5)
                    ), row=1, col=1)

                # Bollinger Bands
                if st.session_state.indikatorler["bollinger"]["aktif"]:
                    ust, orta, alt = bollinger(
                        close,
                        st.session_state.indikatorler["bollinger"]["period"],
                        st.session_state.indikatorler["bollinger"]["std"]
                    )
                    bb_color = st.session_state.indikatorler["bollinger"]["color"]
                    fig.add_trace(go.Scatter(
                        x=df.index, y=ust, mode='lines',
                        name="BB Üst", line=dict(color=bb_color, width=1, dash='dash'),
                        showlegend=True
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=df.index, y=alt, mode='lines',
                        name="BB Alt", line=dict(color=bb_color, width=1, dash='dash'),
                        fill='tonexty', fillcolor=f"rgba(32, 178, 170, 0.1)",
                        showlegend=True
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=df.index, y=orta, mode='lines',
                        name="BB Orta", line=dict(color=bb_color, width=1.5),
                        showlegend=True
                    ), row=1, col=1)

                # Hacim
                if 'Volume' in df.columns:
                    fig.add_trace(go.Bar(
                        x=df.index, y=df['Volume'],
                        name="Hacim", marker_color='rgba(100, 100, 100, 0.3)',
                        showlegend=True
                    ), row=1, col=1)

                # --- ALT GRAFİKLER ---
                current_row = 2

                # RSI
                if st.session_state.indikatorler["rsi"]["aktif"]:
                    rsi_val = rsi(close, st.session_state.indikatorler["rsi"]["period"])
                    fig.add_trace(go.Scatter(
                        x=df.index, y=rsi_val,
                        mode='lines', name="RSI",
                        line=dict(color=st.session_state.indikatorler["rsi"]["color"], width=1.5)
                    ), row=current_row, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
                    fig.update_yaxes(range=[0, 100], row=current_row, col=1)
                    current_row += 1

                # MACD
                if st.session_state.indikatorler["macd"]["aktif"]:
                    macd_line, signal_line, histogram = macd(
                        close,
                        st.session_state.indikatorler["macd"]["fast"],
                        st.session_state.indikatorler["macd"]["slow"],
                        st.session_state.indikatorler["macd"]["signal"]
                    )
                    fig.add_trace(go.Scatter(
                        x=df.index, y=macd_line,
                        mode='lines', name="MACD",
                        line=dict(color='#2196F3', width=1.5)
                    ), row=current_row, col=1)
                    fig.add_trace(go.Scatter(
                        x=df.index, y=signal_line,
                        mode='lines', name="Signal",
                        line=dict(color='#FF9800', width=1.5)
                    ), row=current_row, col=1)
                    fig.add_trace(go.Bar(
                        x=df.index, y=histogram,
                        name="Histogram",
                        marker_color=['#26a69a' if h >= 0 else '#ef5350' for h in histogram.fillna(0)]
                    ), row=current_row, col=1)
                    current_row += 1

                # --- ZOOM & LAYOUT AYARLARI ---
                fig.update_layout(
                    template="plotly_dark",
                    height=600 + (200 * len(alt_grafikler)),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis_rangeslider_visible=False,
                    dragmode='zoom',
                    hovermode='x unified',
                    margin=dict(l=50, r=50, t=80, b=50),
                )

                fig.update_xaxes(rangeslider=dict(visible=False))
                fig.update_yaxes(title_text="Fiyat", row=1, col=1)

                # Zoom butonları
                fig.update_layout(
                    updatemenus=[
                        dict(
                            type="buttons",
                            direction="left",
                            buttons=[
                                dict(count=1, label="1G", step="day", stepmode="backward"),
                                dict(count=7, label="1H", step="day", stepmode="backward"),
                                dict(count=1, label="1A", step="month", stepmode="backward"),
                                dict(count=3, label="3A", step="month", stepmode="backward"),
                                dict(count=6, label="6A", step="month", stepmode="backward"),
                                dict(step="all", label="Tümü"),
                            ],
                            pad={"r": 10, "t": 10},
                            showactive=True,
                            x=0.11,
                            xanchor="left",
                            y=1.12,
                            yanchor="top"
                        ),
                        dict(
                            type="buttons",
                            direction="left",
                            buttons=[
                                dict(method="relayout", args=[{"xaxis.autorange": True, "yaxis.autorange": True}], label="↔️ Sıfırla"),
                            ],
                            pad={"r": 10, "t": 10},
                            x=0.55,
                            xanchor="left",
                            y=1.12,
                            yanchor="top"
                        )
                    ]
                )

                st.plotly_chart(fig, use_container_width=True, config={
                    'scrollZoom': True,
                    'displayModeBar': True,
                    'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
                })

                # Ham veri tablosu
                with st.expander("📋 Ham Veriyi Gör"):
                    st.dataframe(df.tail(50), use_container_width=True)

                # İstatistikler
                with st.expander("📈 İstatistikler"):
                    st.write(df.describe())

                st.caption(f"Son güncelleme: {paket.son_guncelleme.strftime('%Y-%m-%d %H:%M:%S')}")

            except Exception as e:
                st.error(f"❌ Hata: {e}")
                st.info("💡 Yahoo Finance üzerinden denemek için API key girmeden tekrar deneyin.")

    st.divider()
    st.caption("🔧 Çok Kaynaklı Finans Veri Ajanı | Streamlit + Python")

if __name__ == "__main__":
    main()
