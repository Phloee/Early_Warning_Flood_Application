import requests

# Masukkan API Key OpenWeatherMap kamu di bawah ini
API_KEY = "your-openweathermap-api-key"
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Koordinat Jakarta Pusat sebagai contoh
LAT = -6.2088
LON = 106.8456

def test_api_openweather():
    if API_KEY == "your-openweathermap-api-key" or not API_KEY:
        print("PERHATIAN: Kamu belum memasukkan API Key OpenWeatherMap!")
        print("Silakan daftar di https://openweathermap.org/api dan masukkan API_KEY di script ini.\n")

    url = f"{BASE_URL}/weather"
    params = {
        'lat': LAT,
        'lon': LON,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'id'
    }
    
    print("Mengambil data cuaca saat ini (Current Weather) dari OpenWeatherMap")
    print(f"Koordinat: {LAT}, {LON}")
    print("-" * 50)
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            suhu = data.get('main', {}).get('temp')
            kelembapan = data.get('main', {}).get('humidity')
            deskripsi = data['weather'][0]['description'] if data.get('weather') else 'N/A'
            angin = data.get('wind', {}).get('speed')
            nama_lokasi = data.get('name')
            
            print(f"Lokasi          : {nama_lokasi}")
            print(f"Cuaca           : {deskripsi.capitalize()}")
            print(f"Suhu            : {suhu}°C")
            print(f"Kelembapan      : {kelembapan}%")
            print(f"Kecepatan Angin : {angin} m/s")
            print("-" * 50)
        else:
            print(f"Gagal mendapat data! Status code: {response.status_code}")
            print(f"Detail Response: {response.text}")
            
    except Exception as e:
        print(f"Terjadi error saat menghubungi API: {e}")

if __name__ == "__main__":
    test_api_openweather()
