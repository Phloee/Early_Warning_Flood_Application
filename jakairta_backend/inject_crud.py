"""Inject CRUD JS into dashboard home.html"""
import os

crud_js = """
  // ═══════════════════════════ CRUD ═══════════════════════════
  const AREAS_DATA = {% for area in areas_data %}[{ id: {{ area.area.id }}, name: "{{ area.area.name }}" }]{% endfor %};
  function openCrudPanel() {
    const panel = document.getElementById('crudPanel');
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
    loadCamList();
    loadSimList();
  }
  const CAM_IDS = [{% for d in areas_data %}{% if d.cam_id %}{{ d.cam_id }},{% endif %}{% endfor %}];
  const SIM_IDS = [{% for d in areas_data %}{% if d.sim_id %}{{ d.sim_id }},{% endif %}{% endfor %}];

  function renderCamItem(d) {
    const activeStyle = d.is_active ? 'background:rgba(34,197,94,.15);color:#86EFAC;' : 'background:rgba(255,255,255,.06);color:var(--muted);';
    return `<div style="background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:12px;display:flex;align-items:center;gap:10px;">
      <div style="flex:1;min-width:0;">
        <div style="font-size:13px;font-weight:600;">${d.name}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${d.stream_url||'Tidak ada URL'}</div>
        <span style="font-size:10px;padding:2px 7px;border-radius:8px;margin-top:4px;display:inline-block;${activeStyle}">${d.is_active?'Aktif':'Nonaktif'}</span>
      </div>
      <button onclick="openCamModal(${d.id})" style="background:rgba(52,120,246,.15);color:var(--primary);border:none;border-radius:7px;padding:6px 10px;font-size:11px;font-weight:600;cursor:pointer;">Edit</button>
      <button onclick="deleteCam(${d.id},${JSON.stringify(d.name)})" style="background:rgba(239,68,68,.12);color:#FCA5A5;border:none;border-radius:7px;padding:6px 10px;font-size:11px;font-weight:600;cursor:pointer;">Hapus</button>
    </div>`;
  }

  function renderSimItem(d) {
    const fname = d.video_file ? d.video_file.split('/').pop() : 'Tidak ada file';
    const activeStyle = d.is_active ? 'background:rgba(34,197,94,.15);color:#86EFAC;' : 'background:rgba(255,255,255,.06);color:var(--muted);';
    return `<div style="background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:12px;display:flex;align-items:center;gap:10px;">
      <div style="flex:1;min-width:0;">
        <div style="font-size:13px;font-weight:600;">${d.title}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px;">🎬 ${fname}</div>
        <span style="font-size:10px;padding:2px 7px;border-radius:8px;margin-top:4px;display:inline-block;${activeStyle}">${d.is_active?'Aktif':'Nonaktif'}</span>
      </div>
      <button onclick="openSimModal(${d.id})" style="background:rgba(52,120,246,.15);color:var(--primary);border:none;border-radius:7px;padding:6px 10px;font-size:11px;font-weight:600;cursor:pointer;">Edit</button>
      <button onclick="deleteSim(${d.id},${JSON.stringify(d.title)})" style="background:rgba(239,68,68,.12);color:#FCA5A5;border:none;border-radius:7px;padding:6px 10px;font-size:11px;font-weight:600;cursor:pointer;">Hapus</button>
    </div>`;
  }

  async function loadCamList() {
    const el = document.getElementById('camList');
    if (!CAM_IDS.length) { el.innerHTML = '<div style="color:var(--muted);font-size:13px;">Belum ada kamera. Klik &quot;+ Tambah Kamera&quot;</div>'; return; }
    let html = '';
    for (const id of CAM_IDS) {
      const d = await fetch(`/dashboard/camera/${id}/edit/`).then(r=>r.json()).catch(()=>null);
      if (d && d.id) html += renderCamItem(d);
    }
    el.innerHTML = html || '<div style="color:var(--muted);">Tidak ada data.</div>';
  }

  async function loadSimList() {
    const el = document.getElementById('simList');
    if (!SIM_IDS.length) { el.innerHTML = '<div style="color:var(--muted);font-size:13px;">Belum ada video. Klik &quot;+ Tambah Video&quot;</div>'; return; }
    let html = '';
    for (const id of SIM_IDS) {
      const d = await fetch(`/dashboard/sim/${id}/edit/`).then(r=>r.json()).catch(()=>null);
      if (d && d.id) html += renderSimItem(d);
    }
    el.innerHTML = html || '<div style="color:var(--muted);">Tidak ada data.</div>';
  }

  function areaOpts(sel) {
    return AREAS_DATA.map(a=>`<option value="${a.id}"${sel==a.id?' selected':''}>${a.name}</option>`).join('');
  }

  function openCamModal(id=null) {
    document.getElementById('modal-title').textContent = id ? 'Edit Kamera CCTV' : 'Tambah Kamera CCTV';
    document.getElementById('modal-body').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:11px;margin-top:6px;">
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">NAMA KAMERA *</label>
          <input id="camName" placeholder="contoh: CCTV Cipinang-001" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;"></div>
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">WILAYAH</label>
          <select id="camArea" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;">
            <option value="">-- Pilih Wilayah --</option>${areaOpts('')}</select></div>
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">URL EMBED / STREAM CCTV</label>
          <input id="camUrl" placeholder="https://cctv.balitower.co.id/.../embed.html" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;">
          <div style="font-size:11px;color:var(--muted);margin-top:3px;">Paste URL embed dari Bali Tower, Windmill, atau provider CCTV lain</div></div>
        <div style="display:flex;align-items:center;gap:8px;"><input type="checkbox" id="camActive" checked style="width:15px;height:15px;accent-color:var(--primary);">
          <label for="camActive" style="font-size:13px;cursor:pointer;">Aktifkan kamera ini</label></div>
      </div>`;
    document.getElementById('modal-actions').innerHTML = `<button class="mbtn mbtn-cancel" onclick="closeModal()">Batal</button><button class="mbtn mbtn-confirm" onclick="saveCam(${id||'null'})">Simpan</button>`;
    document.getElementById('modal').classList.add('show');
    if (id) fetch(`/dashboard/camera/${id}/edit/`).then(r=>r.json()).then(d=>{
      document.getElementById('camName').value = d.name;
      document.getElementById('camArea').value = d.area_id||'';
      document.getElementById('camUrl').value = d.stream_url||'';
      document.getElementById('camActive').checked = d.is_active;
    });
  }

  async function saveCam(id) {
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken', csrf);
    fd.append('name', document.getElementById('camName').value);
    fd.append('area_id', document.getElementById('camArea').value);
    fd.append('stream_url', document.getElementById('camUrl').value);
    fd.append('is_active', document.getElementById('camActive').checked?'1':'0');
    const url = id ? `/dashboard/camera/${id}/edit/` : '/dashboard/camera/add/';
    const res = await fetch(url,{method:'POST',body:fd}).then(r=>r.json());
    closeModal(); showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1200);
  }

  async function deleteCam(id, name) {
    if (!confirm(`Hapus kamera "${name}"?`)) return;
    const fd = new FormData(); fd.append('csrfmiddlewaretoken', csrf);
    const res = await fetch(`/dashboard/camera/${id}/delete/`,{method:'POST',body:fd}).then(r=>r.json());
    showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1200);
  }

  function openSimModal(id=null) {
    document.getElementById('modal-title').textContent = id ? 'Edit Video Simulasi' : 'Upload Video Simulasi';
    document.getElementById('modal-body').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:11px;margin-top:6px;">
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">JUDUL VIDEO *</label>
          <input id="simTitle" placeholder="contoh: Banjir Jakarta 2024" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;"></div>
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">WILAYAH</label>
          <select id="simArea" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:8px;color:#fff;font-size:13px;font-family:Inter,sans-serif;">
            <option value="">-- Pilih Wilayah --</option>${areaOpts('')}</select></div>
        <div><label style="font-size:11px;color:var(--muted);font-weight:600;">FILE VIDEO (MP4)</label>
          <input type="file" id="simFile" accept="video/mp4,video/*" style="width:100%;margin-top:4px;padding:9px 12px;background:var(--surface2);border:1px solid rgba(245,158,11,.4);border-radius:8px;color:#fff;font-size:12px;font-family:Inter,sans-serif;cursor:pointer;"></div>
        <div style="display:flex;align-items:center;gap:8px;"><input type="checkbox" id="simActive" checked style="width:15px;height:15px;accent-color:var(--warning);">
          <label for="simActive" style="font-size:13px;cursor:pointer;">Aktifkan simulasi ini</label></div>
      </div>`;
    document.getElementById('modal-actions').innerHTML = `<button class="mbtn mbtn-cancel" onclick="closeModal()">Batal</button><button class="mbtn" style="background:var(--warning);color:#000;font-weight:700;" onclick="saveSim(${id||'null'})">Simpan</button>`;
    document.getElementById('modal').classList.add('show');
    if (id) fetch(`/dashboard/sim/${id}/edit/`).then(r=>r.json()).then(d=>{
      document.getElementById('simTitle').value = d.title;
      document.getElementById('simArea').value = d.area_id||'';
      document.getElementById('simActive').checked = d.is_active;
    });
  }

  async function saveSim(id) {
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken', csrf);
    fd.append('title', document.getElementById('simTitle').value);
    fd.append('area_id', document.getElementById('simArea').value);
    fd.append('is_active', document.getElementById('simActive').checked?'1':'0');
    const f = document.getElementById('simFile');
    if (f.files.length > 0) fd.append('video_file', f.files[0]);
    const url = id ? `/dashboard/sim/${id}/edit/` : '/dashboard/sim/add/';
    closeModal(); showToast('Menyimpan...', 'success');
    const res = await fetch(url,{method:'POST',body:fd}).then(r=>r.json());
    showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1500);
  }

  async function deleteSim(id, title) {
    if (!confirm(`Hapus video "${title}"?`)) return;
    const fd = new FormData(); fd.append('csrfmiddlewaretoken', csrf);
    const res = await fetch(`/dashboard/sim/${id}/delete/`,{method:'POST',body:fd}).then(r=>r.json());
    showToast(res.message, res.success?'success':'error');
    if (res.success) setTimeout(()=>location.reload(), 1200);
  }
"""

html_path = os.path.join('templates', 'dashboard', 'home.html')
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove old ending, inject CRUD JS before </script>
old_end = '  }, 1000);\n</script>\n</body>\n</html>\n'
new_end = '  }, 1000);\n' + crud_js + '\n</script>\n</body>\n</html>\n'

if old_end in content:
    content = content.replace(old_end, new_end, 1)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: CRUD JS injected')
else:
    print('PATTERN NOT FOUND — checking end:')
    print(repr(content[-150:]))
