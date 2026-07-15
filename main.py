import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Finans Veri Ajani", page_icon="📊", layout="wide")

# ============================================
# SESSION STATE
# ============================================
def init_session_state():
    if "takip_listesi" not in st.session_state:
        st.session_state.takip_listesi = [
            {"sembol": "AAPL", "isim": "Apple", "tur": "Hisse (ABD)", "aktif": True},
            {"sembol": "MSFT", "isim": "Microsoft", "tur": "Hisse (ABD)", "aktif": True},
            {"sembol": "GOOGL", "isim": "Alphabet", "tur": "Hisse (ABD)", "aktif": True},
            {"sembol": "TSLA", "isim": "Tesla", "tur": "Hisse (ABD)", "aktif": True},
            {"sembol": "NVDA", "isim": "NVIDIA", "tur": "Hisse (ABD)", "aktif": True},
            {"sembol": "THYAO.IS", "isim": "Turk Hava Yollari", "tur": "BIST 100", "aktif": True},
            {"sembol": "GARAN.IS", "isim": "Garanti BBVA", "tur": "BIST 100", "aktif": True},
            {"sembol": "ASELS.IS", "isim": "Aselsan", "tur": "BIST 100", "aktif": True},
            {"sembol": "KCHOL.IS", "isim": "Koc Holding", "tur": "BIST 100", "aktif": True},
            {"sembol": "SISE.IS", "isim": "Sisecam", "tur": "BIST 100", "aktif": True},
            {"sembol": "BIMAS.IS", "isim": "BIM", "tur": "BIST 100", "aktif": True},
            {"sembol": "EREGL.IS", "isim": "Eregli Demir Celik", "tur": "BIST 100", "aktif": True},
            {"sembol": "BTC-USD", "isim": "Bitcoin", "tur": "Kripto", "aktif": True},
            {"sembol": "ETH-USD", "isim": "Ethereum", "tur": "Kripto", "aktif": True},
            {"sembol": "SOL-USD", "isim": "Solana", "tur": "Kripto", "aktif": True},
            {"sembol": "BNB-USD", "isim": "Binance Coin", "tur": "Kripto", "aktif": True},
            {"sembol": "GC=F", "isim": "Altin", "tur": "Emtia", "aktif": True},
            {"sembol": "SI=F", "isim": "Gumus", "tur": "Emtia", "aktif": True},
            {"sembol": "CL=F", "isim": "Ham Petrol (WTI)", "tur": "Emtia", "aktif": True},
            {"sembol": "BZ=F", "isim": "Brent Petrol", "tur": "Emtia", "aktif": True},
            {"sembol": "EURUSD=X", "isim": "EUR/USD", "tur": "Forex", "aktif": True},
            {"sembol": "USDTRY=X", "isim": "USD/TRY", "tur": "Forex", "aktif": True},
            {"sembol": "GBPUSD=X", "isim": "GBP/USD", "tur": "Forex", "aktif": True},
            {"sembol": "XU100.IS", "isim": "BIST 100 Endeks", "tur": "Endeks", "aktif": True},
            {"sembol": "^GSPC", "isim": "S&P 500", "tur": "Endeks", "aktif": True},
            {"sembol": "^IXIC", "isim": "NASDAQ", "tur": "Endeks", "aktif": True},
        ]
    if "indikatorler" not in st.session_state:
        st.session_state.indikatorler = {
            "sma_20": {"aktif": True, "period": 20, "color": "#FFA500"},
            "sma_50": {"aktif": False, "period": 50, "color": "#00CED1"},
            "ema_12": {"aktif": False, "period": 12, "color": "#FF69B4"},
            "rsi": {"aktif": False, "period": 14, "color": "#9370DB"},
            "macd": {"aktif": False, "fast": 12, "slow": 26, "signal": 9},
            "bollinger": {"aktif": False, "period": 20, "std": 2, "color": "#20B2AA"},
        }
    if "custom_indikatorler" not in st.session_state:
        st.session_state.custom_indikatorler = {}
    if "seviyeler" not in st.session_state:
        st.session_state.seviyeler = {}
    if "donusum_noktalari" not in st.session_state:
        st.session_state.donusum_noktalari = {}

init_session_state()

# ============================================
# GENISLETILMIS VARLIK KUTUPHANESI
# ============================================
VARLIK_KUTUPHANESI = {
    "BIST 100": [
        ("THYAO.IS", "Turk Hava Yollari"), ("GARAN.IS", "Garanti BBVA"), ("ASELS.IS", "Aselsan"),
        ("KCHOL.IS", "Koc Holding"), ("SISE.IS", "Sisecam"), ("BIMAS.IS", "BIM"),
        ("EREGL.IS", "Eregli Demir Celik"), ("TUPRS.IS", "Tupras"), ("SAHOL.IS", "Sabanci Holding"),
        ("AKBNK.IS", "Akbank"), ("YKBNK.IS", "Yapi Kredi"), ("ISCTR.IS", "Is Bankasi"),
        ("KRDMD.IS", "Kardemir"), ("PETKM.IS", "Petkim"), ("TOASO.IS", "Tofas"),
        ("ARCLK.IS", "Arcelik"), ("HEKTS.IS", "Hektas"), ("KOZAA.IS", "Koza Altin"),
        ("PGSUS.IS", "Pegasus"), ("TCELL.IS", "Turkcell"), ("SASA.IS", "Sasa Polyester"),
        ("KONTR.IS", "Kontrolmatik"), ("SMRTG.IS", "Smart Guc"), ("ALARK.IS", "Alarko"),
        ("ENKAI.IS", "Enka Insaat"), ("DOHOL.IS", "Dogus Holding"),
    ],
    "Hisse (ABD)": [
        ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("GOOGL", "Alphabet"), ("AMZN", "Amazon"),
        ("TSLA", "Tesla"), ("META", "Meta"), ("NVDA", "NVIDIA"), ("NFLX", "Netflix"),
        ("AMD", "AMD"), ("INTC", "Intel"), ("IBM", "IBM"), ("DIS", "Disney"),
        ("BA", "Boeing"), ("JPM", "JPMorgan"), ("V", "Visa"), ("MA", "Mastercard"),
        ("WMT", "Walmart"), ("KO", "Coca-Cola"), ("PEP", "PepsiCo"), ("PFE", "Pfizer"),
        ("GOOG", "Google"), ("CSCO", "Cisco"), ("NKE", "Nike"), ("MCD", "McDonalds"),
        ("ADBE", "Adobe"), ("CRM", "Salesforce"), ("PYPL", "PayPal"),
    ],
    "Kripto": [
        ("BTC-USD", "Bitcoin"), ("ETH-USD", "Ethereum"), ("BNB-USD", "Binance Coin"),
        ("SOL-USD", "Solana"), ("XRP-USD", "Ripple"), ("ADA-USD", "Cardano"),
        ("DOGE-USD", "Dogecoin"), ("AVAX-USD", "Avalanche"), ("DOT-USD", "Polkadot"),
        ("MATIC-USD", "Polygon"), ("LINK-USD", "Chainlink"), ("LTC-USD", "Litecoin"),
        ("SHIB-USD", "Shiba Inu"), ("TRX-USD", "TRON"), ("UNI-USD", "Uniswap"),
        ("ATOM-USD", "Cosmos"), ("ETC-USD", "Ethereum Classic"),
    ],
    "Emtia": [
        ("GC=F", "Altin"), ("SI=F", "Gumus"), ("CL=F", "Ham Petrol (WTI)"),
        ("BZ=F", "Brent Petrol"), ("NG=F", "Dogalgaz"), ("HG=F", "Bakir"),
        ("PL=F", "Platin"), ("PA=F", "Palladyum"), ("ZC=F", "Misir"),
        ("ZW=F", "Bugday"), ("ZS=F", "Soya Fasulyesi"), ("KC=F", "Kahve"),
        ("CT=F", "Pamuk"), ("SB=F", "Seker"), ("CC=F", "Kakao"),
    ],
    "Forex": [
        ("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("USDJPY=X", "USD/JPY"),
        ("USDCHF=X", "USD/CHF"), ("AUDUSD=X", "AUD/USD"), ("USDCAD=X", "USD/CAD"),
        ("EURGBP=X", "EUR/GBP"), ("EURJPY=X", "EUR/JPY"), ("GBPJPY=X", "GBP/JPY"),
        ("USDTRY=X", "USD/TRY"), ("EURTRY=X", "EUR/TRY"), ("GBPTRY=X", "GBP/TRY"),
        ("AUDJPY=X", "AUD/JPY"), ("CADJPY=X", "CAD/JPY"), ("CHFJPY=X", "CHF/JPY"),
    ],
    "Endeks": [
        ("XU100.IS", "BIST 100"), ("^GSPC", "S&P 500"), ("^DJI", "Dow Jones"),
        ("^IXIC", "NASDAQ"), ("^FTSE", "FTSE 100"), ("^N225", "Nikkei 225"),
        ("^GDAXI", "DAX 40"), ("^FCHI", "CAC 40"), ("^HSI", "Hang Seng"),
        ("^VIX", "VIX"), ("^RUT", "Russell 2000"),
    ],
}

# ============================================
# INDIKATOR FONKSIYONLARI
# ============================================
def sma(seri, period):
    return seri.rolling(window=period).mean()

def ema(seri, period):
    return seri.ewm(span=period, adjust=False).mean()

def rsi(seri, period=14):
    delta = seri.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(seri, fast=12, slow=26, signal=9):
    macd_line = ema(seri, fast) - ema(seri, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger(seri, period=20, std_dev=2):
    orta = sma(seri, period)
    std = seri.rolling(window=period).std()
    ust = orta + (std * std_dev)
    alt = orta - (std * std_dev)
    return ust, orta, alt

# ============================================
# DONUSUM NOKTALARI TESPITI (YUKSELIS/DUSUS)
# ============================================
def donusum_noktalari_bul(df: pd.DataFrame, sembol: str) -> dict:
    """
    Varligin grafikte yukselise gecis ve dususe gecis zamanlarini tespit eder.
    Yerel minimum ve maksimum noktalari bulur, trend degisimlerini isaretler.
    """
    close = df['Close']
    high = df['High']
    low = df['Low']

    # Yerel ekstremumlari bul (pivot noktalari)
    window = 3
    yukselis_noktalari = []   # Yerel minimum -> yukselis baslangici
    dusus_noktalari = []      # Yerel maksimum -> dusus baslangici

    for i in range(window, len(close) - window):
        # Yerel minimum (yukselise gecis noktasi)
        is_local_min = all(close.iloc[i] <= close.iloc[i-j] for j in range(1, window+1)) and \
                       all(close.iloc[i] <= close.iloc[i+j] for j in range(1, window+1))

        # Yerel maksimum (dususe gecis noktasi)
        is_local_max = all(close.iloc[i] >= close.iloc[i-j] for j in range(1, window+1)) and \
                       all(close.iloc[i] >= close.iloc[i+j] for j in range(1, window+1))

        if is_local_min:
            yukselis_noktalari.append({
                "tarih": df.index[i],
                "fiyat": float(close.iloc[i]),
                "tip": "yukselis_baslangici",
                "renk": "green",
                "sembol": "arrow-up"
            })

        if is_local_max:
            dusus_noktalari.append({
                "tarih": df.index[i],
                "fiyat": float(close.iloc[i]),
                "tip": "dusus_baslangici",
                "renk": "red",
                "sembol": "arrow-down"
            })

    # Son donusum noktalarini belirle
    son_donusum = None
    if yukselis_noktalari and dusus_noktalari:
        son_yukselis = yukselis_noktalari[-1]["tarih"]
        son_dusus = dusus_noktalari[-1]["tarih"]
        if son_yukselis > son_dusus:
            son_donusum = {"tip": "yukselis", "tarih": son_yukselis}
        else:
            son_donusum = {"tip": "dusus", "tarih": son_dusus}

    # Trend analizi
    son_10 = close.tail(10)
    trend = "notr"
    if len(son_10) >= 5:
        ilk_5 = son_10.head(5).mean()
        son_5 = son_10.tail(5).mean()
        if son_5 > ilk_5 * 1.02:
            trend = "yukselis"
        elif son_5 < ilk_5 * 0.98:
            trend = "dusus"

    # Destek ve direnc seviyeleri
    son_20 = close.tail(20)
    aktif_destek = float(son_20.min())
    aktif_direnc = float(son_20.max())
    simdiki_fiyat = float(close.iloc[-1])

    # Sinyal
    sinyal = None
    destek_mesafe = ((simdiki_fiyat - aktif_destek) / simdiki_fiyat) * 100 if simdiki_fiyat != 0 else 0
    direnc_mesafe = ((aktif_direnc - simdiki_fiyat) / simdiki_fiyat) * 100 if simdiki_fiyat != 0 else 0

    if destek_mesafe < 2:
        sinyal = "AL"
    elif direnc_mesafe < 2:
        sinyal = "SAT"

    donusumler = {
        "yukselis_noktalari": yukselis_noktalari,
        "dusus_noktalari": dusus_noktalari,
        "son_donusum": son_donusum,
        "trend": trend,
        "aktif_destek": aktif_destek,
        "aktif_direnc": aktif_direnc,
        "simdiki_fiyat": simdiki_fiyat,
        "destek_mesafe": destek_mesafe,
        "direnc_mesafe": direnc_mesafe,
        "sinyal": sinyal
    }

    st.session_state.donusum_noktalari[sembol] = donusumler
    return donusumler


# ============================================
# VERI KAYNAKLARI
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
    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
        pass

    @abstractmethod
    def destekler(self, sembol):
        pass

class YahooFinanceKaynagi(VeriKaynagi):
    def __init__(self):
        self.isim = "Yahoo Finance"
        self.gecikme = "15dk gecikme"

    def destekler(self, sembol):
        return True

    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
        interval_map = {"1d": "1d", "1h": "1h", "15m": "15m", "5m": "5m", "1m": "1m"}
        interval = interval_map.get(periyot, "1d")
        try:
            ticker = yf.Ticker(sembol)
            if periyot in ["1m", "5m", "15m"]:
                df = ticker.history(period="7d", interval=interval)
            else:
                df = ticker.history(period="6mo", interval=interval)
            if df.empty:
                raise ValueError("Veri bulunamadi")
            return VeriPaketi(sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                              veri=df, gecikme="15dk gecikme", son_guncelleme=datetime.now())
        except Exception as e:
            raise Exception(f"Yahoo Finance hatasi: {e}")

class AlphaVantageKaynagi(VeriKaynagi):
    def __init__(self, api_key):
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

    def destekler(self, sembol):
        return True

    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
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
            return VeriPaketi(sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                              veri=df, gecikme="15dk gecikme", son_guncelleme=datetime.now())
        except Exception as e:
            raise Exception(f"Alpha Vantage hatasi: {e}")

class TwelveDataKaynagi(VeriKaynagi):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.isim = "Twelve Data"
        self.gecikme = "15dk gecikme (ucretsiz)"

    def destekler(self, sembol):
        return True

    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
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
            return VeriPaketi(sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                              veri=df, gecikme="15dk gecikme (ucretsiz)", son_guncelleme=datetime.now())
        except Exception as e:
            raise Exception(f"Twelve Data hatasi: {e}")

# ============================================
# INVESTING.COM ANLIK VERI
# ============================================
class InvestingComAnlik:
    def __init__(self):
        self.base_url = "https://www.investing.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        self.pair_ids = {
            "THYAO.IS": "43687", "GARAN.IS": "43696", "ASELS.IS": "43680",
            "KCHOL.IS": "43702", "SISE.IS": "43691", "BIMAS.IS": "43683",
            "EREGL.IS": "43688", "TUPRS.IS": "43695", "SAHOL.IS": "43690",
            "AKBNK.IS": "43678", "YKBNK.IS": "43700", "ISCTR.IS": "43698",
            "KRDMD.IS": "43701", "PETKM.IS": "43689", "TOASO.IS": "43693",
            "ARCLK.IS": "43681", "HEKTS.IS": "43697", "KOZAA.IS": "43703",
            "PGSUS.IS": "43692", "TCELL.IS": "43694",
            "AAPL": "6408", "MSFT": "252", "GOOGL": "6369", "AMZN": "6435",
            "TSLA": "13994", "META": "14240", "NVDA": "13842", "NFLX": "13063",
            "AMD": "8274", "INTC": "251", "IBM": "8088", "DIS": "250",
            "BA": "238", "JPM": "244", "V": "13916", "MA": "13917",
            "WMT": "211", "KO": "9593", "PEP": "242", "PFE": "131",
            "BTC-USD": "945629", "ETH-USD": "997650", "BNB-USD": "1158819",
            "SOL-USD": "1177189", "XRP-USD": "1118146", "ADA-USD": "1072724",
            "DOGE-USD": "1098080", "AVAX-USD": "1147622", "DOT-USD": "1137848",
            "MATIC-USD": "1131142", "LINK-USD": "1121700", "LTC-USD": "1061443",
            "GC=F": "8830", "SI=F": "8836", "CL=F": "8849",
            "BZ=F": "8862", "NG=F": "8861", "HG=F": "8831",
            "PL=F": "8910", "PA=F": "8911", "ZC=F": "8918",
            "ZW=F": "8917", "ZS=F": "8916", "KC=F": "8832",
            "EURUSD=X": "1", "GBPUSD=X": "2", "USDJPY=X": "3",
            "USDCHF=X": "4", "AUDUSD=X": "5", "USDCAD=X": "7",
            "EURGBP=X": "6", "EURJPY=X": "9", "GBPJPY=X": "11",
            "USDTRY=X": "18", "EURTRY=X": "37", "GBPTRY=X": "36",
            "XU100.IS": "178", "^GSPC": "166", "^DJI": "169",
            "^IXIC": "14958", "^FTSE": "27", "^N225": "178",
            "^GDAXI": "172", "^FCHI": "167", "^HSI": "179",
        }

    def fiyat_cek(self, sembol):
        if sembol not in self.pair_ids:
            return {"hata": f"Investing.com: {sembol} icin pair ID bulunamadi"}

        pair_id = self.pair_ids[sembol]

        try:
            url = f"{self.base_url}/instruments/Service/GetTechincalData"
            payload = {"pairID": pair_id, "period": 86400, "viewType": "normal"}
            response = requests.post(url, data=payload, headers=self.headers, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "technicalSummary" in data:
                        return {
                            "fiyat": float(data.get("last", 0)),
                            "degisim": float(data.get("change", 0)),
                            "degisim_yuzde": float(data.get("changePercent", 0)),
                            "yuksek": float(data.get("high", 0)),
                            "dusuk": float(data.get("low", 0)),
                            "hacim": int(data.get("volume", 0)),
                            "kaynak": "Investing.com",
                            "hata": None
                        }
                except:
                    pass

            url2 = f"{self.base_url}/instruments/FinancialInstrumentChart/GetInstrumentParam?pairID={pair_id}"
            response2 = requests.get(url2, headers=self.headers, timeout=10)

            if response2.status_code == 200:
                try:
                    data2 = response2.json()
                    if "info" in data2:
                        info = data2["info"]
                        return {
                            "fiyat": float(info.get("last", 0) or info.get("last_dir", 0)),
                            "degisim": float(info.get("change", 0)),
                            "degisim_yuzde": float(info.get("changePercent", 0)),
                            "yuksek": float(info.get("high", 0)),
                            "dusuk": float(info.get("low", 0)),
                            "hacim": int(info.get("volume", 0) or 0),
                            "kaynak": "Investing.com",
                            "hata": None
                        }
                except:
                    pass

            return {"hata": "Investing.com'dan veri alinamadi"}

        except Exception as e:
            return {"hata": f"Investing.com hatasi: {e}"}

class InvestingComKaynagi(VeriKaynagi):
    def __init__(self):
        self.isim = "Investing.com"
        self.gecikme = "Gercek zamanli / 1dk gecikme"
        self.anlik = InvestingComAnlik()

    def destekler(self, sembol):
        return sembol in self.anlik.pair_ids

    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
        try:
            yahoo = YahooFinanceKaynagi()
            paket = yahoo.veri_cek(sembol, periyot, baslangic, bitis)
            paket.kaynak = self.isim
            paket.gecikme = self.gecikme
            return paket
        except Exception as e:
            raise Exception(f"Investing.com hatasi: {e}")

class MockVeriKaynagi(VeriKaynagi):
    def __init__(self, seed=42):
        self.isim = "Mock Veri"
        self.gecikme = "Gercek zamanli (simule)"
        self.seed = seed

    def destekler(self, sembol):
        return True

    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
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
        return VeriPaketi(sembol=sembol, kaynak=self.isim, zaman_dilimi=periyot,
                          veri=df, gecikme="Simule (test verisi)", son_guncelleme=datetime.now())

class AkilliVeriKoordinatoru:
    def __init__(self):
        self.kaynaklar = []

    def kaynak_ekle(self, kaynak, oncelik=0):
        self.kaynaklar.append((oncelik, kaynak))
        self.kaynaklar.sort(key=lambda x: x[0])

    def veri_cek(self, sembol, periyot="1d", baslangic=None, bitis=None):
        for oncelik, kaynak in self.kaynaklar:
            if not kaynak.destekler(sembol):
                continue
            try:
                return kaynak.veri_cek(sembol, periyot, baslangic, bitis)
            except Exception:
                continue
        raise Exception("Tum veri kaynaklari basarisiz oldu!")


# ============================================
# ANLIK FIYAT CEKME
# ============================================
@st.cache_data(ttl=30)
def anlik_fiyat_cek(sembol, alpha_key="", twelve_key=""):
    hatalar = []

    try:
        inv = InvestingComAnlik()
        veri = inv.fiyat_cek(sembol)
        if not veri.get("hata"):
            return veri
        hatalar.append(f"Investing: {veri.get('hata')}")
    except Exception as e:
        hatalar.append(f"Investing: {e}")

    try:
        ticker = yf.Ticker(sembol)
        hist = ticker.history(period="2d")
        if not hist.empty and len(hist) >= 1:
            son_kapanis = hist['Close'].iloc[-1]
            onceki_kapanis = hist['Close'].iloc[-2] if len(hist) > 1 else son_kapanis
            degisim = son_kapanis - onceki_kapanis
            degisim_yuzde = (degisim / onceki_kapanis) * 100 if onceki_kapanis != 0 else 0
            return {
                "fiyat": son_kapanis, "degisim": degisim, "degisim_yuzde": degisim_yuzde,
                "hacim": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
                "yuksek": hist['High'].iloc[-1], "dusuk": hist['Low'].iloc[-1],
                "kaynak": "Yahoo Finance", "hata": None
            }
    except Exception as e:
        hatalar.append(f"Yahoo: {e}")

    if twelve_key:
        try:
            url = f"https://api.twelvedata.com/quote?symbol={sembol}&apikey={twelve_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if "close" in data:
                fiyat = float(data["close"])
                onceki = float(data.get("previous_close", fiyat))
                degisim = fiyat - onceki
                degisim_yuzde = (degisim / onceki) * 100 if onceki != 0 else 0
                return {
                    "fiyat": fiyat, "degisim": degisim, "degisim_yuzde": degisim_yuzde,
                    "hacim": int(data.get("volume", 0)),
                    "yuksek": float(data.get("high", fiyat)), "dusuk": float(data.get("low", fiyat)),
                    "kaynak": "Twelve Data", "hata": None
                }
        except Exception as e:
            hatalar.append(f"Twelve: {e}")

    if alpha_key:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={sembol}&apikey={alpha_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if "Global Quote" in data and data["Global Quote"]:
                gq = data["Global Quote"]
                fiyat = float(gq["05. price"])
                onceki = float(gq["08. previous close"])
                degisim = fiyat - onceki
                degisim_yuzde = float(gq["10. change percent"].replace('%', ''))
                return {
                    "fiyat": fiyat, "degisim": degisim, "degisim_yuzde": degisim_yuzde,
                    "hacim": int(gq["06. volume"]),
                    "yuksek": float(gq["03. high"]), "dusuk": float(gq["04. low"]),
                    "kaynak": "Alpha Vantage", "hata": None
                }
        except Exception as e:
            hatalar.append(f"Alpha: {e}")

    return {"hata": f"Tum kaynaklar basarisiz: {'; '.join(hatalar)}"}

# ============================================
# OZEL INDIKATOR YUKLEME
# ============================================
def custom_indikator_ekle(isim, kod):
    try:
        local_ns = {}
        exec(kod, {"pd": pd, "np": np, "sma": sma, "ema": ema, "rsi": rsi, "macd": macd, "bollinger": bollinger}, local_ns)

        func = None
        for key, val in local_ns.items():
            if callable(val) and not key.startswith('_'):
                func = val
                break

        if func is None:
            return False, "Fonksiyon bulunamadi. 'def indikator_adi(df, ...)' seklinde tanimlayin."

        st.session_state.custom_indikatorler[isim] = {
            "fonksiyon": func,
            "kod": kod,
            "aktif": True,
            "color": "#FFD700",
            "tip": "cizgi",
            "panel": "ana"
        }
        return True, f"✅ '{isim}' indikatoru eklendi!"
    except Exception as e:
        return False, f"❌ Hata: {e}"

def custom_indikator_sil(isim):
    if isim in st.session_state.custom_indikatorler:
        del st.session_state.custom_indikatorler[isim]
        return True
    return False


# ============================================
# STREAMLIT UI
# ============================================
def main():
    st.title("📊 Cok Kaynakli Finans Veri Ajani")
    st.markdown("**Investing.com → Twelve Data → Alpha Vantage → Yahoo Finance → Mock** sirasiyla en guvenilir veriyi bulur.")

    with st.sidebar:
        st.header("⚙️ Ayarlar")

        with st.expander("🔑 API Anahtarlari", expanded=False):
            alpha_key = st.text_input("Alpha Vantage API Key", type="password")
            twelve_key = st.text_input("Twelve Data API Key", type="password")

        periyot = st.selectbox("Zaman Dilimi",
                              ["1d", "1h", "15m", "5m", "1m"],
                              format_func=lambda x: {"1d": "📅 Gunluk", "1h": "🕐 Saatlik",
                                                     "15m": "⏱️ 15 Dakika", "5m": "⏱️ 5 Dakika", "1m": "⏱️ 1 Dakika"}[x])

        st.divider()

        st.subheader("📈 Temel Indikatorler")
        ind_col1, ind_col2 = st.columns(2)
        with ind_col1:
            st.session_state.indikatorler["sma_20"]["aktif"] = st.checkbox("SMA 20", value=st.session_state.indikatorler["sma_20"]["aktif"])
            st.session_state.indikatorler["sma_50"]["aktif"] = st.checkbox("SMA 50", value=st.session_state.indikatorler["sma_50"]["aktif"])
            st.session_state.indikatorler["ema_12"]["aktif"] = st.checkbox("EMA 12", value=st.session_state.indikatorler["ema_12"]["aktif"])
        with ind_col2:
            st.session_state.indikatorler["rsi"]["aktif"] = st.checkbox("RSI", value=st.session_state.indikatorler["rsi"]["aktif"])
            st.session_state.indikatorler["macd"]["aktif"] = st.checkbox("MACD", value=st.session_state.indikatorler["macd"]["aktif"])
            st.session_state.indikatorler["bollinger"]["aktif"] = st.checkbox("Bollinger", value=st.session_state.indikatorler["bollinger"]["aktif"])

        st.divider()

        st.subheader("➕ Ozel Indikator Ekle")
        with st.expander("Yeni Indikator", expanded=False):
            yeni_isim = st.text_input("Indikator Adi", placeholder="ornek_indikator", key="custom_name")

            ornek_kodu = "def my_indicator(df, period=14):\n    close = df['Close']\n    return close.rolling(window=period).mean()"
            yeni_kod = st.text_area("Python Kodu", height=200, value=ornek_kodu, key="custom_code")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 Kaydet", use_container_width=True, key="btn_save_custom"):
                    if yeni_isim and yeni_kod:
                        ok, msg = custom_indikator_ekle(yeni_isim, yeni_kod)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Isim ve kod gerekli!")
            with col_b:
                st.button("🧪 Test Et", use_container_width=True, key="btn_test_custom", disabled=True)

        if st.session_state.custom_indikatorler:
            st.markdown("---")
            st.caption("📌 Ozel Indikatorlerim:")
            for isim, ind in list(st.session_state.custom_indikatorler.items()):
                col_x, col_y = st.columns([3, 1])
                with col_x:
                    ind["aktif"] = st.checkbox(f"🔧 {isim}", value=ind.get("aktif", True), key=f"custom_{isim}")
                with col_y:
                    if st.button("🗑️", key=f"del_custom_{isim}"):
                        custom_indikator_sil(isim)
                        st.rerun()

        st.divider()

        st.subheader("📋 Takip Listem")
        with st.expander("➕ Varlik Ekle", expanded=False):
            tur_secimi = st.selectbox("Kategori", list(VARLIK_KUTUPHANESI.keys()), key="add_cat")
            varliklar = VARLIK_KUTUPHANESI[tur_secimi]
            varlik_secimi = st.selectbox("Varlik", varliklar, format_func=lambda x: f"{x[0]} - {x[1]}", key="add_var")
            if st.button("Listeye Ekle", use_container_width=True, key="btn_add"):
                mevcut_semboller = [v["sembol"] for v in st.session_state.takip_listesi]
                if varlik_secimi[0] not in mevcut_semboller:
                    st.session_state.takip_listesi.append({
                        "sembol": varlik_secimi[0], "isim": varlik_secimi[1],
                        "tur": tur_secimi, "aktif": True
                    })
                    st.success(f"✅ {varlik_secimi[1]} eklendi!")
                    st.rerun()
                else:
                    st.warning("⚠️ Zaten listede!")

        st.markdown("---")
        for i, varlik in enumerate(st.session_state.takip_listesi):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{varlik['sembol']}**  <br><small>{varlik['isim']} | {varlik['tur']}</small>", unsafe_allow_html=True)
            with col_b:
                if st.button("🗑️", key=f"sil_{i}", help=f"{varlik['isim']} sil"):
                    st.session_state.takip_listesi.pop(i)
                    st.rerun()

        st.divider()
        use_mock = st.checkbox("🧪 Mock Veri Kullan (Test)", value=False)

    # ==================== ANA ICERIK ====================

    st.subheader("💰 Anlik Piyasa Verileri")
    aktif_varliklar = [v for v in st.session_state.takip_listesi if v.get("aktif", True)]

    if aktif_varliklar:
        cols_per_row = 4
        rows = [aktif_varliklar[i:i+cols_per_row] for i in range(0, len(aktif_varliklar), cols_per_row)]

        for row in rows:
            cols = st.columns(len(row))
            for col, varlik in zip(cols, row):
                with col:
                    with st.spinner(f"⏳ {varlik['sembol']}..."):
                        veri = anlik_fiyat_cek(varlik["sembol"], alpha_key, twelve_key)

                    if veri.get("hata"):
                        st.error(f"❌ {varlik['sembol']}: Veri alinamadi")
                    else:
                        fiyat = veri["fiyat"]
                        degisim = veri["degisim"]
                        degisim_yuzde = veri["degisim_yuzde"]
                        kaynak = veri.get("kaynak", "Bilinmiyor")
                        renk = "🟢" if degisim >= 0 else "🔴"
                        isaret = "+" if degisim >= 0 else ""

                        st.metric(
                            label=f"{renk} {varlik['isim']} ({varlik['sembol']})",
                            value=f"{fiyat:,.4f}" if fiyat < 1 else f"{fiyat:,.2f}",
                            delta=f"{isaret}{degisim_yuzde:.2f}% ({isaret}{degisim:,.4f})" if fiyat < 1 else f"{isaret}{degisim_yuzde:.2f}% ({isaret}{degisim:,.2f})",
                            delta_color="normal"
                        )
                        st.caption(f"📡 {kaynak} | Hacim: {veri['hacim']:,} | Yuksek: {veri['yuksek']:.2f} | Dusuk: {veri['dusuk']:.2f}")
    else:
        st.info("📭 Takip listeniz bos. Sidebar'dan varlik ekleyin.")

    st.divider()

    st.subheader("📊 Detayli Grafik")
    secenekler = [(v["sembol"], f"{v['isim']} ({v['sembol']})") for v in st.session_state.takip_listesi]
    if secenekler:
        secili = st.selectbox("Grafik icin sembol sec", secenekler, format_func=lambda x: x[1])
        secili_sembol = secili[0]
    else:
        secili_sembol = st.text_input("Sembol girin (orn: AAPL)", value="AAPL")

    if st.button("🚀 Grafigi Ciz", type="primary", use_container_width=True):
        with st.spinner("Tum kaynaklar deneniyor..."):
            koordinator = AkilliVeriKoordinatoru()
            koordinator.kaynak_ekle(InvestingComKaynagi(), 1)
            if twelve_key:
                koordinator.kaynak_ekle(TwelveDataKaynagi(twelve_key), 2)
            if alpha_key:
                koordinator.kaynak_ekle(AlphaVantageKaynagi(alpha_key), 3)
            koordinator.kaynak_ekle(YahooFinanceKaynagi(), 4)
            if use_mock:
                koordinator.kaynak_ekle(MockVeriKaynagi(), 99)

            try:
                paket = koordinator.veri_cek(secili_sembol, periyot)
                df = paket.veri

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📡 Kaynak", paket.kaynak)
                col2.metric("⏱️ Gecikme", paket.gecikme)
                col3.metric("📊 Veri Sayisi", f"{len(df)} satir")
                col4.metric("💵 Son Kapanis", f"{df['Close'].iloc[-1]:.4f}" if df['Close'].iloc[-1] < 1 else f"{df['Close'].iloc[-1]:.2f}")

                st.success(f"✅ {paket.kaynak} uzerinden veri alindi!")

                # Donusum noktalari analizi
                with st.spinner("Donusum noktalari analiz ediliyor..."):
                    donusumler = donusum_noktalari_bul(df, secili_sembol)

                # Donusum seviyeleri kartlari
                seviye_col1, seviye_col2, seviye_col3, seviye_col4 = st.columns(4)
                simdiki = donusumler["simdiki_fiyat"]
                destek = donusumler["aktif_destek"]
                direnc = donusumler["aktif_direnc"]

                seviye_col1.metric("📍 Simdiki Fiyat", f"{simdiki:.2f}")
                seviye_col2.metric("🟢 Destek", f"{destek:.2f}", delta=f"-{donusumler['destek_mesafe']:.1f}%", delta_color="inverse")
                seviye_col3.metric("🔴 Direnc", f"{direnc:.2f}", delta=f"+{donusumler['direnc_mesafe']:.1f}%", delta_color="inverse")

                if donusumler.get("sinyal"):
                    sinyal_renk = {"AL": "🟢", "SAT": "🔴"}
                    seviye_col4.markdown(f"### {sinyal_renk.get(donusumler['sinyal'], '⚪')} {donusumler['sinyal']}")
                else:
                    seviye_col4.metric("⚖️ Durum", "Notr")

                # Trend bilgisi
                trend_emoji = {"yukselis": "📈", "dusus": "📉", "notr": "⚖️"}
                st.info(f"{trend_emoji.get(donusumler['trend'], '⚪')} Mevcut Trend: {donusumler['trend'].upper()}")

                # Donusum noktalari ozeti
                yukselis_sayisi = len(donusumler["yukselis_noktalari"])
                dusus_sayisi = len(donusumler["dusus_noktalari"])
                st.caption(f"📊 Tespit Edilen: {yukselis_sayisi} yukselis noktasi, {dusus_sayisi} dusus noktasi")

                # Grafik cizimi
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

                # Candlestick
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    name=secili_sembol, increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
                ), row=1, col=1)

                # Destek ve Direnc cizgileri
                fig.add_hline(y=destek, line_dash="dash", line_color="green", 
                             annotation_text=f"Destek: {destek:.2f}", row=1, col=1)
                fig.add_hline(y=direnc, line_dash="dash", line_color="red",
                             annotation_text=f"Direnc: {direnc:.2f}", row=1, col=1)

                # Donusum noktalari - yukselis (yesil oklar)
                for nokta in donusumler["yukselis_noktalari"][-5:]:
                    fig.add_trace(go.Scatter(
                        x=[nokta["tarih"]], y=[nokta["fiyat"]],
                        mode='markers',
                        marker=dict(symbol='arrow-up', size=15, color='green'),
                        name=f"📈 Yukselis {nokta['tarih'].strftime('%m-%d')}",
                        showlegend=False
                    ), row=1, col=1)

                # Donusum noktalari - dusus (kirmizi oklar)
                for nokta in donusumler["dusus_noktalari"][-5:]:
                    fig.add_trace(go.Scatter(
                        x=[nokta["tarih"]], y=[nokta["fiyat"]],
                        mode='markers',
                        marker=dict(symbol='arrow-down', size=15, color='red'),
                        name=f"📉 Dusus {nokta['tarih'].strftime('%m-%d')}",
                        showlegend=False
                    ), row=1, col=1)

                close = df['Close']

                if st.session_state.indikatorler["sma_20"]["aktif"]:
                    sma20 = sma(close, 20)
                    fig.add_trace(go.Scatter(x=df.index, y=sma20, mode='lines', name="SMA 20", line=dict(color="#FFA500", width=1.5)), row=1, col=1)

                if st.session_state.indikatorler["sma_50"]["aktif"]:
                    sma50 = sma(close, 50)
                    fig.add_trace(go.Scatter(x=df.index, y=sma50, mode='lines', name="SMA 50", line=dict(color="#00CED1", width=1.5)), row=1, col=1)

                if st.session_state.indikatorler["ema_12"]["aktif"]:
                    ema12 = ema(close, 12)
                    fig.add_trace(go.Scatter(x=df.index, y=ema12, mode='lines', name="EMA 12", line=dict(color="#FF69B4", width=1.5)), row=1, col=1)

                if st.session_state.indikatorler["bollinger"]["aktif"]:
                    ust, orta, alt = bollinger(close, 20, 2)
                    fig.add_trace(go.Scatter(x=df.index, y=ust, mode='lines', name="BB Ust", line=dict(color="#20B2AA", width=1, dash='dash')), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=alt, mode='lines', name="BB Alt", line=dict(color="#20B2AA", width=1, dash='dash'), fill='tonexty', fillcolor="rgba(32, 178, 170, 0.1)"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=orta, mode='lines', name="BB Orta", line=dict(color="#20B2AA", width=1.5)), row=1, col=1)

                # Ozel indikatorler (ana panel)
                for isim, ind in st.session_state.custom_indikatorler.items():
                    if ind.get("aktif") and ind.get("panel", "ana") == "ana":
                        try:
                            sonuc = ind["fonksiyon"](df)
                            if isinstance(sonuc, pd.Series):
                                fig.add_trace(go.Scatter(x=df.index, y=sonuc, mode='lines', name=f"🔧 {isim}", line=dict(color=ind.get("color", "#FFD700"), width=1.5)), row=1, col=1)
                        except Exception as e:
                            st.warning(f"🔧 {isim} indikatoru calistirilamadi: {e}")

                if 'Volume' in df.columns:
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Hacim", marker_color='rgba(100, 100, 100, 0.3)'), row=1, col=1)

                current_row = 2

                if st.session_state.indikatorler["rsi"]["aktif"]:
                    rsi_val = rsi(close, 14)
                    fig.add_trace(go.Scatter(x=df.index, y=rsi_val, mode='lines', name="RSI", line=dict(color="#9370DB", width=1.5)), row=current_row, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
                    fig.update_yaxes(range=[0, 100], row=current_row, col=1)
                    current_row += 1

                if st.session_state.indikatorler["macd"]["aktif"]:
                    macd_line, signal_line, histogram = macd(close, 12, 26, 9)
                    fig.add_trace(go.Scatter(x=df.index, y=macd_line, mode='lines', name="MACD", line=dict(color='#2196F3', width=1.5)), row=current_row, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=signal_line, mode='lines', name="Signal", line=dict(color='#FF9800', width=1.5)), row=current_row, col=1)
                    fig.add_trace(go.Bar(x=df.index, y=histogram, name="Histogram", marker_color=['#26a69a' if h >= 0 else '#ef5350' for h in histogram.fillna(0)]), row=current_row, col=1)
                    current_row += 1

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

                fig.update_layout(
                    updatemenus=[
                        dict(
                            type="buttons",
                            direction="left",
                            buttons=[
                                dict(method="relayout", label="1G", args=[{"xaxis.range": [df.index[-1] - pd.Timedelta(days=1), df.index[-1]]}]),
                                dict(method="relayout", label="1H", args=[{"xaxis.range": [df.index[-1] - pd.Timedelta(days=7), df.index[-1]]}]),
                                dict(method="relayout", label="1A", args=[{"xaxis.range": [df.index[-1] - pd.Timedelta(days=30), df.index[-1]]}]),
                                dict(method="relayout", label="3A", args=[{"xaxis.range": [df.index[-1] - pd.Timedelta(days=90), df.index[-1]]}]),
                                dict(method="relayout", label="6A", args=[{"xaxis.range": [df.index[-1] - pd.Timedelta(days=180), df.index[-1]]}]),
                                dict(method="relayout", label="Tumu", args=[{"xaxis.autorange": True}]),
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
                                dict(method="relayout", args=[{"xaxis.autorange": True, "yaxis.autorange": True}], label="↔️ Sifirla"),
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

                with st.expander("📋 Ham Veriyi Gor"):
                    st.dataframe(df.tail(50), use_container_width=True)

                with st.expander("📈 Istatistikler"):
                    st.write(df.describe())

                with st.expander("🎯 Donusum Noktalari Detayi"):
                    col_y, col_d = st.columns(2)
                    with col_y:
                        st.markdown("**📈 Yukselis Noktalari (Son 5)**")
                        for nokta in donusumler["yukselis_noktalari"][-5:]:
                            st.write(f"  {nokta['tarih'].strftime('%Y-%m-%d')}: {nokta['fiyat']:.2f}")
                    with col_d:
                        st.markdown("**📉 Dusus Noktalari (Son 5)**")
                        for nokta in donusumler["dusus_noktalari"][-5:]:
                            st.write(f"  {nokta['tarih'].strftime('%Y-%m-%d')}: {nokta['fiyat']:.2f}")

                    st.markdown("---")
                    st.write(f"**Son 20 bar Destek:** {destek:.4f}")
                    st.write(f"**Son 20 bar Direnc:** {direnc:.4f}")
                    st.write(f"**Destek Mesafe:** %{donusumler['destek_mesafe']:.2f}")
                    st.write(f"**Direnc Mesafe:** %{donusumler['direnc_mesafe']:.2f}")

                st.caption(f"Son guncelleme: {paket.son_guncelleme.strftime('%Y-%m-%d %H:%M:%S')}")

            except Exception as e:
                st.error(f"❌ Hata: {e}")
                import traceback
                st.code(traceback.format_exc())

    st.divider()
    st.caption("🔧 Cok Kaynakli Finans Veri Ajani v5.0 | Investing.com + Ozel Indikatorler + Donusum Noktalari")

if __name__ == "__main__":
    main()
