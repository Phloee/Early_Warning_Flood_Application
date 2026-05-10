import os
import django
from datetime import timedelta
from django.utils import timezone
import random

# Konfigurasi agar bisa mengakses database Django secara mandiri (Standalone)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.weather.models import WeatherData, WeatherForecast
from apps.weather.services import ARIMAPredictorService

def run_simulation():
    print("--- MULAI SIMULASI ---")
    print("Mempersiapkan data bohongan (Mock) History Cuaca untuk 48 Jam terakhir...")
    
    # Hapus data sebelumnya agar bersih saat dites
    WeatherData.objects.filter(source=WeatherData.Source.OPENWEATHER).delete()
    WeatherForecast.objects.filter(source='openweather_arima_ml').delete()
    
    # Menghasilkan 48 jam riwayat cuaca secara berurutan
    base_time = timezone.now() - timedelta(hours=48)
    for i in range(48):
        rec_time = base_time + timedelta(hours=i)
        
        # Buat pola fiktif: Siang itu lebih panas & kering, malam lebih dingin & lembab.
        jam = rec_time.hour
        if 8 <= jam <= 16: # Siang panas
            t = round(random.uniform(29.0, 33.0), 1)
            h = round(random.uniform(60.0, 75.0), 1)
            r = 0.0
        else: # Malam/pagi dingin, kemungkinan hujan (kelembapan tinggi)
            t = round(random.uniform(25.0, 28.0), 1)
            h = round(random.uniform(80.0, 95.0), 1)
            r = round(random.uniform(0.0, 2.0), 1)
            
        # Skenario Khusus: 3 jam terakhir sebelum sekarang tiba-tiba hujan deras (Pola Banjir)
        if i >= 45:
            r = round(random.uniform(15.0, 25.0), 1) # Hujan sangat lebat di 3 jam terakhir
            
        WeatherData.objects.create(
            area=None,
            source=WeatherData.Source.OPENWEATHER,
            temperature=t,
            humidity=h,
            rainfall=r,
            wind_speed=random.uniform(5.0, 15.0),
            description="Mock Historical Data",
            weather_code="800",
            raw_data={},
            recorded_at=rec_time
        )
        
    print(f"Selesai! 48 baris data tiruan berhasil ditaruh ke database (Selesai pada {base_time + timedelta(hours=47)}).")
    print(f"Catatan: Saya menyuntikkan skenario HUJAN DERAS di 3 jam terakhir agar kita melihat apakah ARIMA bisa memprediksi potensi banjir.")
    
    print("\n[AI MEMPROSES] Mesin auto_arima (ARIMA) melacak pola curah hujan, suhu, dan kelembapan...")
    print("Harap tunggu beberapa detik (mesin komputasi butuh waktu memecahkan statistiknya)...\n")
    
    # NYALAKAN PREDIKSI MACHINE LEARNING!
    success = ARIMAPredictorService.predict_next_5_hours()
    
    if success:
        print("=== HASIL PROYEKSI MASA DEPAN DARI MESIN ARIMA ===")
        forecasts = WeatherForecast.objects.filter(source='openweather_arima_ml').order_by('forecast_time')
        for f in forecasts:
            waktu_lokal = f.forecast_time.astimezone().strftime("%d %b %Y, Pukul %H:%M WIB")
            print(f"> {waktu_lokal} | Curah Hujan: {f.rainfall} mm/h | Suhu: {f.temperature} C | Status: {f.description}")
        print("===================================================\nSelesai! Keseluruhan data di atas otomatis masuk ke tabel database-mu.")
    else:
        print("!! Gagal menjalankan prediksi ARIMA. (pmdarima/statsmodels belum sepenuhnya terunduh atau error lain)")
        print("Buka view terminal sebelumnya atau pastikan requirements tuntas diinstall.")

if __name__ == "__main__":
    run_simulation()
