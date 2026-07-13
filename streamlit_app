import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Finans Veri Ajanı", page_icon="📊", layout="wide")

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

# ================= STREAMLIT UI =================

def main():
    st.title("📊 Çok Kaynaklı Finans Veri Ajanı")
    st.markdown("Yahoo Finance, Alpha Vantage, Twelve Data ve Mock veri kaynaklarını kullanır.")

    # Sidebar - Ayarlar
    with st.sidebar:
        st.header("⚙️ Ayarlar")

        sembol = st.text_input("Sembol", value="AAPL", 
                               help="Örn: AAPL, THYAO.IS, BTC-USD, GARAN.IS")

        periyot = st.selectbox("Zaman Dilimi", 
                              ["1d", "1h", "15m", "5m", "1m"],
                              format_func=lambda x: {"1d": "Günlük", "1h": "Saatlik", 
                                                     "15m": "15 Dakika", "5m": "5 Dakika", "1m": "1 Dakika"}[x])

        st.divider()
        st.subheader("🔑 API Anahtarları (İsteğe Bağlı)")
        alpha_key = st.text_input("Alpha Vantage API Key", type="password")
        twelve_key = st.text_input("Twelve Data API Key", type="password")

        st.divider()
        use_mock = st.checkbox("🧪 Mock Veri Kullan (Test)", value=False)

        st.divider()
        st.info("💡 **Yahoo Finance** her zaman ücretsiz çalışır.\n"
                "**Alpha Vantage** ve **Twelve Data** için API key gerekir.")

    # Ana içerik
    col1, col2, col3 = st.columns(3)

    if st.button("🚀 Veri Çek", type="primary", use_container_width=True):
        with st.spinner("Veri kaynakları deneniyor..."):
            koordinator = AkilliVeriKoordinatoru()

            # Kaynakları ekle (öncelik sırasına göre)
            if twelve_key:
                koordinator.kaynak_ekle(TwelveDataKaynagi(twelve_key), 1)
            if alpha_key:
                koordinator.kaynak_ekle(AlphaVantageKaynagi(alpha_key), 2)

            koordinator.kaynak_ekle(YahooFinanceKaynagi(), 3)

            if use_mock:
                koordinator.kaynak_ekle(MockVeriKaynagi(), 99)

            try:
                paket = koordinator.veri_cek(sembol, periyot)

                # Başarılı bilgileri
                col1.metric("📡 Kaynak", paket.kaynak)
                col2.metric("⏱️ Gecikme", paket.gecikme)
                col3.metric("📊 Veri Sayısı", f"{len(paket.veri)} satır")

                st.success(f"✅ {paket.kaynak} üzerinden veri alındı!")

                # Candlestick grafiği
                fig = go.Figure(data=[go.Candlestick(
                    x=paket.veri.index,
                    open=paket.veri['Open'],
                    high=paket.veri['High'],
                    low=paket.veri['Low'],
                    close=paket.veri['Close'],
                    name=sembol
                )])

                fig.update_layout(
                    title=f"{sembol} - {periyot} Grafiği",
                    yaxis_title="Fiyat",
                    xaxis_title="Tarih",
                    template="plotly_dark",
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

                # Veri tablosu
                with st.expander("📋 Ham Veriyi Gör"):
                    st.dataframe(paket.veri.tail(50), use_container_width=True)

                # İstatistikler
                with st.expander("📈 İstatistikler"):
                    st.write(paket.veri.describe())

                # Son güncelleme
                st.caption(f"Son güncelleme: {paket.son_guncelleme.strftime('%Y-%m-%d %H:%M:%S')}")

            except Exception as e:
                st.error(f"❌ Hata: {e}")
                st.info("💡 Yahoo Finance üzerinden denemek için API key girmeden tekrar deneyin.")

    # Footer
    st.divider()
    st.caption("🔧 Çok Kaynaklı Finans Veri Ajanı | Streamlit + Python")

if __name__ == "__main__":
    main()
