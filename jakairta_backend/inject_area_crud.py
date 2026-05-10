import os

# 1. Update urls.py
urls_path = r"c:\Users\Phloe\OneDrive\Documents\EARLY WARNING FLOOD\jakairta_backend\apps\dashboard\urls.py"
with open(urls_path, "r", encoding="utf-8") as f:
    urls_content = f.read()

if "area/add/" not in urls_content:
    new_urls = """
    # CRUD — Wilayah
    path('area/add/', views.area_add, name='dashboard_area_add'),
    path('area/<int:area_id>/edit/', views.area_edit, name='dashboard_area_edit'),
    path('area/<int:area_id>/delete/', views.area_delete, name='dashboard_area_delete'),
"""
    urls_content = urls_content.replace(
        "path('camera/add/', views.camera_add, name='dashboard_camera_add'),",
        new_urls + "    path('camera/add/', views.camera_add, name='dashboard_camera_add'),"
    )
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(urls_content)
    print("urls.py updated")

# 2. Update views.py
views_path = r"c:\Users\Phloe\OneDrive\Documents\EARLY WARNING FLOOD\jakairta_backend\apps\dashboard\views.py"
with open(views_path, "r", encoding="utf-8") as f:
    views_content = f.read()

if "def area_add(" not in views_content:
    new_views = """
# ─── CRUD: Area ──────────────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def area_add(request):
    from apps.areas.models import Area
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        district = request.POST.get('district', '').strip()
        lat = request.POST.get('latitude', '-6.200000')
        lon = request.POST.get('longitude', '106.816666')
        if not name or not district:
            return JsonResponse({'success': False, 'message': 'Nama & Distrik wajib diisi.'})
        area = Area.objects.create(name=name, district=district, latitude=lat, longitude=lon, is_active=True)
        return JsonResponse({'success': True, 'message': 'Wilayah berhasil ditambahkan.', 'id': area.id})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

@login_required(login_url='/dashboard/login/')
def area_edit(request, area_id):
    from apps.areas.models import Area
    area = Area.objects.filter(id=area_id).first()
    if not area:
        return JsonResponse({'success': False, 'message': 'Wilayah tidak ditemukan.'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'id': area.id, 'name': area.name, 'district': area.district, 'latitude': float(area.latitude), 'longitude': float(area.longitude)})
    if request.method == 'POST':
        area.name = request.POST.get('name', area.name).strip()
        area.district = request.POST.get('district', area.district).strip()
        area.latitude = request.POST.get('latitude', area.latitude)
        area.longitude = request.POST.get('longitude', area.longitude)
        area.save()
        return JsonResponse({'success': True, 'message': 'Wilayah berhasil diupdate.'})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

@login_required(login_url='/dashboard/login/')
@require_POST
def area_delete(request, area_id):
    from apps.areas.models import Area
    area = Area.objects.filter(id=area_id).first()
    if not area:
        return JsonResponse({'success': False, 'message': 'Wilayah tidak ditemukan.'}, status=404)
    area.is_active = False # Soft delete
    area.save()
    return JsonResponse({'success': True, 'message': 'Wilayah berhasil dihapus.'})
"""
    with open(views_path, "a", encoding="utf-8") as f:
        f.write(new_views)
    print("views.py updated")

# 3. Update home.html
html_path = r"c:\Users\Phloe\OneDrive\Documents\EARLY WARNING FLOOD\jakairta_backend\templates\dashboard\home.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Add button to Kondisi Wilayah header
old_sec_header = """<div class="sec-header">
    <span class="sec-title">Kondisi Wilayah</span>
    <div class="sec-line"></div>
  </div>"""

new_sec_header = """<div class="sec-header">
    <span class="sec-title">Kondisi Wilayah</span>
    <div class="sec-line"></div>
    <button onclick="openAreaModal()" style="background:var(--primary);color:#fff;border:none;border-radius:8px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;">+ Tambah Wilayah</button>
  </div>"""

if 'openAreaModal()' not in html_content:
    html_content = html_content.replace(old_sec_header, new_sec_header)

# Add Edit/Del buttons to area card
old_ac_header = """<div class="ac-name">{{ d.area.name }} <span style="font-size:12px;color:var(--muted);font-weight:500;">(Live)</span></div>"""
new_ac_header = """<div class="ac-name">{{ d.area.name }} <span style="font-size:12px;color:var(--muted);font-weight:500;">(Live)</span>
              <button onclick="openAreaModal({{ d.area.id }})" style="background:rgba(52,120,246,0.15);color:var(--primary);border:none;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600;cursor:pointer;margin-left:8px;">Edit</button>
              <button onclick="deleteArea({{ d.area.id }}, '{{ d.area.name|escapejs }}')" style="background:rgba(239,68,68,0.15);color:#FCA5A5;border:none;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600;cursor:pointer;margin-left:4px;">Del</button>
            </div>"""

if 'openAreaModal({{ d.area.id }})' not in html_content:
    html_content = html_content.replace(old_ac_header, new_ac_header)

# Add JS functions
js_inject = """
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
      </div>`;
    document.getElementById('modal-actions').innerHTML = `<button class="mbtn mbtn-cancel" onclick="closeModal()">Batal</button><button class="mbtn mbtn-confirm" onclick="saveArea(${id||'null'})">Simpan</button>`;
    document.getElementById('modal').classList.add('show');
    if (id) fetch(`/dashboard/area/${id}/edit/`).then(r=>r.json()).then(d=>{
      if (d.id) {
        document.getElementById('areaName').value = d.name;
        document.getElementById('areaDistrict').value = d.district;
        document.getElementById('areaLat').value = d.latitude;
        document.getElementById('areaLon').value = d.longitude;
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
    const url = id ? `/dashboard/area/${id}/edit/` : '/dashboard/area/add/';
    const res = await fetch(url,{method:'POST',body:fd}).then(r=>r.json());
    closeModal(); showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1200);
  }

  async function deleteArea(id, name) {
    if (!confirm(`Yakin ingin menghapus wilayah "${name}"?`)) return;
    const fd = new FormData(); fd.append('csrfmiddlewaretoken', csrf);
    const res = await fetch(`/dashboard/area/${id}/delete/`,{method:'POST',body:fd}).then(r=>r.json());
    showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1200);
  }
"""

if "async function saveArea(id)" not in html_content:
    html_content = html_content.replace('</script>', js_inject + '\n</script>')

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("home.html updated")
