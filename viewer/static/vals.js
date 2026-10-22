const LEGAL_MAX = 83;          // 2483 MHz, top of the ISM band
const WIN = 3;                 // channels needed by a 2 Mbps link
const avg = new Array(N).fill(0);
const pk  = new Array(N).fill(0);
let samples = 0;

function updatePlanner(vals) {
  samples++;
  for (let i = 0; i < N; i++) {
    avg[i] += (vals[i] - avg[i]) * 0.05;          // slow average
    pk[i] = Math.max(vals[i], pk[i] * 0.995);     // decaying peak
  }
  const score = i => 0.7 * avg[i] + 0.3 * pk[i];

  // score every possible window, quietest first
  const wins = [];
  for (let c = 0; c + WIN - 1 <= LEGAL_MAX; c++) {
    let s = 0;
    for (let k = 0; k < WIN; k++) s += score(c + k);
    wins.push({ ch: c + 1, s: s / WIN });          // ch = window center
  }
  wins.sort((a, b) => a.s - b.s);

  // pick up to 3 channels at least 6 apart (hop list)
  const hop = [];
  for (const w of wins) {
    if (hop.every(h => Math.abs(h.ch - w.ch) >= 6)) hop.push(w);
    if (hop.length === 3) break;
  }

  const best = hop[0];
  const risk = best.s < 3 ? "LOW" : best.s < 15 ? "MEDIUM" : "HIGH";
  const $ = id => document.getElementById(id);

  $("pl-status").textContent = samples < 50 ? "Learning the band... " + samples + "/50"
                                            : "Recommendation ready";
  $("pl-best").textContent = best.ch;
  $("pl-freq").textContent = (2400 + best.ch) + " MHz";
  $("pl-risk").textContent = risk + " (" + best.s.toFixed(1) + "%)";
  $("pl-hop").textContent  = hop.map(h => h.ch).join(", ");
  $("pl-code").textContent = "radio.setChannel(" + best.ch + ");";

  // Wi-Fi load: mean activity within +-5 NRF channels of each Wi-Fi center (5n+7)
  for (const n of [1, 6, 11]) {
    const c = 5 * n + 7; let s = 0, k = 0;
    for (let i = c - 5; i <= c + 5; i++) { s += avg[i]; k++; }
    $("pl-w" + n).textContent = (s / k).toFixed(1) + "%";
  }
  let tot = 0;
  for (let i = 0; i <= LEGAL_MAX; i++) tot += avg[i];
  $("pl-load").textContent = (tot / (LEGAL_MAX + 1)).toFixed(1) + "%";
}