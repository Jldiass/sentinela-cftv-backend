let cameras = [];
const players = [];
const API = "/api/v1";

const esc = (value) => String(value ?? "").replace(
  /[&<>"']/g,
  (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char],
);

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error((await response.json()).detail || "Falha na operação");
  return response.json();
}

document.querySelectorAll(".tab").forEach((button) => {
  button.onclick = () => {
    document.querySelectorAll(".tab,.page").forEach((element) => element.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.page).classList.add("active");
  };
});

function attach(video, url) {
  if (Hls.isSupported()) {
    const player = new Hls({ lowLatencyMode: true });
    player.loadSource(url);
    player.attachMedia(video);
    players.push(player);
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = url;
  }
}

async function loadAll() {
  cameras = await api(`${API}/cameras`);
  const online = cameras.filter((camera) => camera.status === "online").length;
  const unstable = cameras.filter((camera) => camera.status === "unstable").length;
  const offline = cameras.length - online - unstable;
  document.getElementById("summary").textContent = `${online} online · ${unstable} instável · ${offline} offline · ${cameras.length}/8 cadastradas`;
  players.splice(0).forEach((player) => player.destroy());

  const grid = document.getElementById("grid");
  grid.innerHTML = cameras.length
    ? cameras.map((camera) => `<article class="tile"><video id="v${camera.id}" controls muted playsinline></video><div class="tilebar"><span>${esc(camera.name)}<small> · ${esc(camera.location)}</small></span><span class="status ${camera.status}">● ${camera.status}</span></div></article>`).join("")
    : '<div class="empty">Cadastre a primeira câmera para começar.</div>';
  cameras.filter((camera) => camera.status !== "offline").forEach((camera) => attach(document.getElementById(`v${camera.id}`), camera.hls_url));

  document.getElementById("cameraList").innerHTML = cameras.map((camera) => `<div class="camera-row"><div><strong>${esc(camera.name)}</strong><div class="copy">${esc(camera.rtmp_url)}</div></div><span class="status ${camera.status}">${camera.status}</span></div>`).join("");
  document.getElementById("historyCamera").innerHTML = cameras.map((camera) => `<option value="${camera.id}">${esc(camera.name)}</option>`).join("");
  await loadEvents();
}

document.getElementById("cameraForm").onsubmit = async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const body = {
    name: form.get("name"), location: form.get("location"), audio_enabled: form.has("audio_enabled"),
    pre_alarm_seconds: +form.get("pre_alarm_seconds"),
    post_alarm_seconds: +form.get("post_alarm_seconds"),
  };
  const message = document.getElementById("formMsg");
  try {
    const camera = await api(`${API}/cameras`, { method: "POST", body: JSON.stringify(body) });
    message.innerHTML = `Cadastrada. Publique em:<br><span class="copy">${esc(camera.rtmp_url)}</span>`;
    event.target.reset();
    await loadAll();
  } catch (error) {
    message.textContent = error.message;
  }
};

async function findRecordings() {
  const id = document.getElementById("historyCamera").value;
  if (!id) return;
  const params = new URLSearchParams();
  const start = document.getElementById("historyStart").value;
  const end = document.getElementById("historyEnd").value;
  if (start) params.set("start", new Date(start).toISOString());
  if (end) params.set("end", new Date(end).toISOString());
  try {
    const rows = await api(`${API}/cameras/${id}/recordings?${params}`);
    document.getElementById("recordings").innerHTML = rows.length
      ? rows.map((row) => `<div class="recording-row"><span>${new Date(row.start).toLocaleString()} · ${Math.round(row.duration)}s</span><a target="_blank" href="${esc(row.url)}">Abrir</a></div>`).join("")
      : "<p>Nenhuma gravação neste período.</p>";
  } catch (error) {
    document.getElementById("recordings").textContent = error.message;
  }
}

async function loadEvents() {
  const rows = await api(`${API}/events`);
  document.getElementById("events").innerHTML = rows.length
    ? rows.map((event) => `<div class="event-row"><span>${esc(event.kind)} · câmera ${event.camera_id}<small> · ${new Date(event.happened_at).toLocaleString()} · ${esc(event.clip_status)}</small></span>${event.playback_url ? `<a target="_blank" href="${esc(event.playback_url)}">Ver clipe</a>` : "<span>Vídeo indisponível</span>"}</div>`).join("")
    : "<p>Nenhum evento registrado.</p>";
}

loadAll();
setInterval(loadAll, 15000);
