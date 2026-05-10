import os

# 1. Update views.py
views_path = r"c:\Users\Phloe\OneDrive\Documents\EARLY WARNING FLOOD\jakairta_backend\apps\dashboard\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    views_content = f.read()

new_area_add = """@login_required(login_url='/dashboard/login/')
def area_add(request):
    from apps.areas.models import Area
    from apps.cctv.models import CCTVCamera
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        district = request.POST.get('district', '').strip()
        lat = request.POST.get('latitude', '-6.200000')
        lon = request.POST.get('longitude', '106.816666')
        cctv_url = request.POST.get('cctv_url', '').strip()
        
        if not name or not district:
            return JsonResponse({'success': False, 'message': 'Nama & Distrik wajib diisi.'})
        area = Area.objects.create(name=name, district=district, latitude=lat, longitude=lon, is_active=True)
        
        if cctv_url:
            CCTVCamera.objects.create(name=f"CCTV {name}", area=area, stream_url=cctv_url, is_active=True)
            
        return JsonResponse({'success': True, 'message': 'Wilayah berhasil ditambahkan.', 'id': area.id})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)"""

new_area_edit = """@login_required(login_url='/dashboard/login/')
def area_edit(request, area_id):
    from apps.areas.models import Area
    from apps.cctv.models import CCTVCamera
    area = Area.objects.filter(id=area_id).first()
    if not area:
        return JsonResponse({'success': False, 'message': 'Wilayah tidak ditemukan.'}, status=404)
        
    cam = area.cameras.filter(is_active=True).first()
    cctv_url = cam.stream_url if cam else ''
    
    if request.method == 'GET':
        return JsonResponse({'id': area.id, 'name': area.name, 'district': area.district, 'latitude': float(area.latitude), 'longitude': float(area.longitude), 'cctv_url': cctv_url})
    if request.method == 'POST':
        area.name = request.POST.get('name', area.name).strip()
        area.district = request.POST.get('district', area.district).strip()
        area.latitude = request.POST.get('latitude', area.latitude)
        area.longitude = request.POST.get('longitude', area.longitude)
        area.save()
        
        new_cctv_url = request.POST.get('cctv_url', '').strip()
        if new_cctv_url:
            if cam:
                cam.stream_url = new_cctv_url
                cam.save()
            else:
                CCTVCamera.objects.create(name=f"CCTV {area.name}", area=area, stream_url=new_cctv_url, is_active=True)
        elif cam and not new_cctv_url:
            cam.is_active = False
            cam.save()
            
        return JsonResponse({'success': True, 'message': 'Wilayah berhasil diupdate.'})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)"""

import re
views_content = re.sub(r"@login_required.*?def area_add\(request\):.*?return JsonResponse\(\{'success': False, 'message': 'Method not allowed\.'\}, status=405\)", new_area_add, views_content, flags=re.DOTALL)
views_content = re.sub(r"@login_required.*?def area_edit\(request, area_id\):.*?return JsonResponse\(\{'success': False, 'message': 'Method not allowed\.'\}, status=405\)", new_area_edit, views_content, flags=re.DOTALL)

with open(views_path, "w", encoding="utf-8") as f:
    f.write(views_content)
print("views.py updated")

# 2. Update home.html
html_path = r"c:\Users\Phloe\OneDrive\Documents\EARLY WARNING FLOOD\jakairta_backend\templates\dashboard\home.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

new_js = """
  function openAreaModal(id=null) {
    document.getElementById('modal-title').textContent = id ? 'Edit Wilayah' : 'Tambah Wilayah';
    document.getElementById('modal-body').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:11px;margin-top:6px;">
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">NAMA WILAYAH *</label>
          <input id="areaName" placeholder="contoh: Kampung Melayu" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;"></div>
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">KOTA / KABUPATEN *</label>
          <input id="areaDistrict" placeholder="contoh: Jakarta Timur" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;"></div>
        <div style="display:flex;gap:10px;">
          <div style="flex:1;"><label style="font-size:11px;color:var(--muted);font-weight:600;">LATITUDE</label>
            <input id="areaLat" value="-6.200000" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;"></div>
          <div style="flex:1;"><label style="font-size:11px;color:var(--muted);font-weight:600;">LONGITUDE</label>
            <input id="areaLon" value="106.816666" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;"></div>
        </div>
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">URL CCTV (HTML/Embed) (Opsional)</label>
          <input id="areaCctvUrl" placeholder="https://..." style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;">
          <div style="font-size:10px;color:var(--muted);margin-top:3px;">Jika diisi, CCTV otomatis ditambahkan ke wilayah ini.</div>
        </div>
      </div>`;
    document.getElementById('modal-actions').innerHTML = `<button class="mbtn mbtn-cancel" onclick="closeModal()">Batal</button><button class="mbtn mbtn-confirm" onclick="saveArea(${id||'null'})">Simpan</button>`;
    document.getElementById('modal').classList.add('show');
    if (id) fetch(`/dashboard/area/${id}/edit/`).then(r=>r.json()).then(d=>{
      if (d.id) {
        document.getElementById('areaName').value = d.name;
        document.getElementById('areaDistrict').value = d.district;
        document.getElementById('areaLat').value = d.latitude;
        document.getElementById('areaLon').value = d.longitude;
        document.getElementById('areaCctvUrl').value = d.cctv_url || '';
      }
    });
  }

  async function saveArea(id) {
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken', csrf);
    fd.append('name', document.getElementById('areaName').value);
    fd.append('district', document.getElementById('areaDistrict').value);
    fd.append('latitude', document.getElementById('areaLat').value);
    fd.append('longitude', document.getElementById('areaLon').value);
    fd.append('cctv_url', document.getElementById('areaCctvUrl').value);
    const url = id ? `/dashboard/area/${id}/edit/` : '/dashboard/area/add/';
    const res = await fetch(url,{method:'POST',body:fd}).then(r=>r.json());
    closeModal(); showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1200);
  }
"""

html_content = re.sub(r"function openAreaModal\(id=null\).*?async function saveArea\(id\).*?setTimeout\(\(\)=>location\.reload\(\), 1200\);\n  }", new_js, html_content, flags=re.DOTALL)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("home.html updated")
