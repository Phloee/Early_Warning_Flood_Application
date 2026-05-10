import requests

def test_api_bmkg():
    # Contoh untuk wilayah Gambir, Jakarta Pusat
    kode_wilayah = '31.71.01.1001'
    url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_wilayah}"
    
    print(f"Mengambil data cuaca dari: {url}")
    print("-" * 50)
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        lokasi = data.get('lokasi', {})
        print(f"Wilayah: {lokasi.get('desa')}, {lokasi.get('kecamatan')}, {lokasi.get('kotkab')}")
        print("-" * 50)
        
        # Ambil data cuaca (cukup ambil dari slot waktu yang pertama - biasanya data per jam)
        for item in data.get('data', []):
            cuaca_slots = item.get('cuaca', [])
            
            # Karena cuaca adalah list of list, kita ratakan dan ambil 5 pertama
            semua_cuaca = [entry for slot in cuaca_slots for entry in slot]
            
            for cuaca in semua_cuaca[:5]:
                waktu = cuaca.get('local_datetime')
                suhu = cuaca.get('t')
                kelembapan = cuaca.get('hu')
                deskripsi = cuaca.get('weather_desc')
                
                print(f"Waktu : {waktu}")
                print(f"Cuaca : {deskripsi}")
                print(f"Suhu  : {suhu}°C")
                print(f"Kelembapan : {kelembapan}%")
                print("-" * 25)
    else:
        print(f"Gagal mendapat data! Status code: {response.status_code}")

if __name__ == "__main__":
    test_api_bmkg()
