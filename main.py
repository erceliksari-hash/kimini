"""
Çok Kaynaklı Finans Veri Ajanı
- Yahoo Finance (yedek)
- Alpha Vantage (alternatif)
- Twelve Data (dakikalık + Türk borsası)
- Mock veri (test için)
"""

import yfinance as yf
import requests
import pandas as pd
import numpy as np          # ← BUNU EKLE
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass
import time


@dataclass
class VeriPaketi:
    sembol: str
    kaynak: str
    zaman_dilimi: str  # "1d", "1h", "15m", "5m", "1m"
    veri: pd.DataFrame
    gecikme: str  # "gerçek zamanlı", "15dk gecikme", "günlük"
    son_guncelleme: datetime


# ============================================
# ABSTRACT BASE CLASS - Tüm veri kaynakları
# ============================================
class VeriKaynagi(ABC):
    """Tüm veri kaynakları için temel sınıf."""
    
    @abstractmethod
    def veri_cek(self, sembol: str, periyot: str = "1d", 
                 baslangic: Optional[str] = None, 
                 bitis: Optional[str] = None) -> VeriPaketi:
        pass
    
    @abstractmethod
    def destekler(self, sembol: str) -> bool:
        """Bu sembolü destekliyor mu?"""
        pass


# ============================================
# 1. YAHOO FINANCE (Yedek / Temel)
# ============================================
class YahooFinanceKaynagi(VeriKaynagi):
    """
    Yahoo Finance - Ücretsiz ama gecikmeli.
    Günlük ve haftalık veri için yeterli.
    """
    
    def __init__(self):
        self.isim = "Yahoo Finance"
        self.gecikme = "15dk gecikme (ABD), günlük (diğer)"
    
    def destekler(self, sembol: str) -> bool:
        # Hemen hemen her sembolü destekler
        return True
    
    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        
        interval_map = {
            "1d": "1d", "1h": "1h", "15m": "15m", 
            "5m": "5m", "1m": "1m"
        }
        interval = interval_map.get(periyot, "1d")
        
        try:
            ticker = yf.Ticker(sembol)
            
            # Periyoda göre period belirle
            if periyot in ["1m", "5m", "15m"]:
                # Dakikalık veri sadece son 7 gün
                df = ticker.history(period="7d", interval=interval)
            else:
                df = ticker.history(period="6mo", interval=interval)
            
            if df.empty:
                raise ValueError("Veri bulunamadı")
            
            return VeriPaketi(
                sembol=sembol,
                kaynak=self.isim,
                zaman_dilimi=periyot,
                veri=df,
                gecikme="15dk gecikme",
                son_guncelleme=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Yahoo Finance hatası: {e}")


# ============================================
# 2. ALPHA VANTAGE (Alternatif)
# ============================================
class AlphaVantageKaynagi(VeriKaynagi):
    """
    Alpha Vantage - API key gerektirir.
    Daha stabil veri, 5 API çağrısı/dakika (ücretsiz).
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.isim = "Alpha Vantage"
        self.gecikme = "15dk gecikme"
        self._son_cagri = 0  # Rate limiting
    
    def _rate_limit(self):
        """5 çağrı/dakika limiti."""
        gecen = time.time() - self._son_cagri
        if gecen < 12:  # 12 saniye bekle
            time.sleep(12 - gecen)
        self._son_cagri = time.time()
    
    def destekler(self, sembol: str) -> bool:
        return True  # Çoğu sembol desteklenir
    
    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        
        self._rate_limit()
        
        function_map = {
            "1d": "TIME_SERIES_DAILY",
            "1h": "TIME_SERIES_INTRADAY",  # 60min
            "15m": "TIME_SERIES_INTRADAY",
            "5m": "TIME_SERIES_INTRADAY",
            "1m": "TIME_SERIES_INTRADAY"
        }
        
        function = function_map.get(periyot, "TIME_SERIES_DAILY")
        
        params = {
            "function": function,
            "symbol": sembol,
            "apikey": self.api_key,
            "outputsize": "full"
        }
        
        if periyot != "1d":
            interval_map = {"1h": "60min", "15m": "15min", 
                          "5m": "5min", "1m": "1min"}
            params["interval"] = interval_map.get(periyot, "5min")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            # Veriyi DataFrame'e çevir
            time_series_key = [k for k in data.keys() if "Time Series" in k][0]
            df_data = data[time_series_key]
            
            df = pd.DataFrame.from_dict(df_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Sütun isimlerini düzelt
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df.astype(float)
            
            return VeriPaketi(
                sembol=sembol,
                kaynak=self.isim,
                zaman_dilimi=periyot,
                veri=df,
                gecikme="15dk gecikme",
                son_guncelleme=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Alpha Vantage hatası: {e}")


# ============================================
# 3. TWELVE DATA (Dakikalık + Türk Borsası)
# ============================================
class TwelveDataKaynagi(VeriKaynagi):
    """
    Twelve Data - Türk borsasını destekler (BIST).
    Freemium: 800 API çağrısı/gün.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.isim = "Twelve Data"
        self.gecikme = "Gerçek zamanlı (ücretli) / 15dk gecikme (ücretsiz)"
    
    def destekler(self, sembol: str) -> bool:
        # BIST sembolleri: THYAO.IS, GARAN.IS, vb.
        return True
    
    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        
        interval_map = {
            "1d": "1day", "1h": "1h", "15m": "15min",
            "5m": "5min", "1m": "1min"
        }
        interval = interval_map.get(periyot, "1day")
        
        params = {
            "symbol": sembol,
            "interval": interval,
            "apikey": self.api_key,
            "outputsize": 5000
        }
        
        if baslangic:
            params["start_date"] = baslangic
        if bitis:
            params["end_date"] = bitis
        
        try:
            response = requests.get(
                f"{self.base_url}/time_series", 
                params=params, timeout=10
            )
            data = response.json()
            
            if "values" not in data:
                raise ValueError(data.get("message", "Bilinmeyen hata"))
            
            df = pd.DataFrame(data["values"])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df = df.sort_index()
            df = df.astype(float)
            
            return VeriPaketi(
                sembol=sembol,
                kaynak=self.isim,
                zaman_dilimi=periyot,
                veri=df,
                gecikme="15dk gecikme (ücretsiz)",
                son_guncelleme=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Twelve Data hatası: {e}")


# ============================================
# 4. MOCK VERİ (Test ve Geliştirme)
# ============================================
class MockVeriKaynagi(VeriKaynagi):
    """Test için rastgele ama tutarlı veri üretir."""
    
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
        
        # Son 30 gün için veri üret
        gun_sayisi = 30 if periyot == "1d" else 7 * 24 * 60  # dakika için
        if periyot != "1d":
            # Dakikalık için daha az veri
            gun_sayisi = 7 * 24 * 12  # 5 dakikalık = 12 bar/saat
        
        if periyot == "1d":
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        elif periyot == "1h":
            dates = pd.date_range(end=datetime.now(), periods=7*24, freq='H')
        elif periyot == "15m":
            dates = pd.date_range(end=datetime.now(), periods=7*24*4, freq='15min')
        else:
            dates = pd.date_range(end=datetime.now(), periods=1000, freq='5min')
        
        # Rastgele ama tutarlı fiyat hareketi (random walk)
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
            sembol=sembol,
            kaynak=self.isim,
            zaman_dilimi=periyot,
            veri=df,
            gecikme="Simüle (test verisi)",
            son_guncelleme=datetime.now()
        )


# ============================================
# KOORDİNATÖR - Akıllı Kaynak Seçimi
# ============================================
class AkilliVeriKoordinatoru:
    """
    Birden fazla veri kaynağını yönetir.
    Bir kaynak başarısız olursa diğerine geçer.
    """
    
    def __init__(self):
        self.kaynaklar: List[VeriKaynagi] = []
        self.kaynak_sirasi = []  # Öncelik sırası
    
    def kaynak_ekle(self, kaynak: VeriKaynagi, oncelik: int = 0):
        self.kaynaklar.append((oncelik, kaynak))
        self.kaynaklar.sort(key=lambda x: x[0])
    
    def veri_cek(self, sembol: str, periyot: str = "1d",
                 baslangic: Optional[str] = None,
                 bitis: Optional[str] = None) -> VeriPaketi:
        
        print(f"\n🔍 {sembol} için veri aranıyor...")
        print(f"   İstenen periyot: {periyot}")
        
        for oncelik, kaynak in self.kaynaklar:
            print(f"\n   📡 Deneniyor: {kaynak.isim}")
            
            if not kaynak.destekler(sembol):
                print(f"   ⚠️  {kaynak.isim} bu sembolü desteklemiyor.")
                continue
            
            try:
                paket = kaynak.veri_cek(sembol, periyot, baslangic, bitis)
                print(f"   ✅ Başarılı! Kaynak: {kaynak.isim}")
                print(f"   📊 {len(paket.veri)} satır veri alındı.")
                print(f"   ⏱️  Gecikme: {paket.gecikme}")
                return paket
                
            except Exception as e:
                print(f"   ❌ Hata: {str(e)[:80]}")
                continue
        
        raise Exception("Tüm veri kaynakları başarısız oldu!")


# ============================================
# KULLANIM ÖRNEĞİ
# ============================================
if __name__ == "__main__":
    
    # Koordinatör oluştur
    koordinator = AkilliVeriKoordinatoru()
    
    # Kaynakları ekle (öncelik sırasına göre)
    # 1. Twelve Data (Türk borsası için en iyi)
    # koordinator.kaynak_ekle(TwelveDataKaynagi("SENIN_API_KEY"), 1)
    
    # 2. Alpha Vantage
    # koordinator.kaynak_ekle(AlphaVantageKaynagi("SENIN_API_KEY"), 2)
    
    # 3. Yahoo Finance (yedek)
    koordinator.kaynak_ekle(YahooFinanceKaynagi(), 3)
    
    # 4. Mock veri (test için)
    koordinator.kaynak_ekle(MockVeriKaynagi(), 99)
    
    # Test: Farklı senaryolar
    testler = [
        ("AAPL", "1d", "Günlük ABD hissesi"),
        ("THYAO.IS", "1d", "Türk Hava Yolları (Yahoo)"),
        ("BTC-USD", "1h", "Saatlik Bitcoin"),
    ]
    
    for sembol, periyot, aciklama in testler:
        print(f"\n{'='*60}")
        print(f"🧪 TEST: {aciklama}")
        print(f"{'='*60}")
        try:
            paket = koordinator.veri_cek(sembol, periyot)
            print(f"\n📋 SONUÇ:")
            print(f"   Son kapanış: ${paket.veri['Close'].iloc[-1]:.2f}")
            print(f"   Veri aralığı: {paket.veri.index[0]} → {paket.veri.index[-1]}")
        except Exception as e:
            print(f"\n💥 Tüm kaynaklar başarısız: {e}")
