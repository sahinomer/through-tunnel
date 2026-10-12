// Smooth client-side rendering of the vehicle on the Leaflet map.
//
// Why: the server pushes UI updates at ~16 Hz while the browser draws at 60-75 fps, so a
// server-moved marker holds still for several frames and then jumps (5-9 px at 5x / zoom 17).
// Instead, the server sends the (decimated) ground-truth track once and re-anchors this clock on
// every play/pause/seek/speed change; each animation frame interpolates the position locally.
// The server remains authoritative for the playback time; nothing here affects the simulation.
window.ttPlayer = (() => {
  const s = { map: null, layers: null, track: null, extras: [], t0: 0, wall0: 0, rate: 1, playing: false, trailIdx: -1, raf: 0 };

  const findLayer = (id) => {
    let found = null;
    s.map.eachLayer((l) => { if (l.id === id) found = l; });
    return found;
  };

  const now = () => {
    if (!s.playing) return s.t0;
    return Math.min(s.t0 + ((performance.now() - s.wall0) / 1000) * s.rate, s.track.t[s.track.t.length - 1]);
  };

  // Largest i with ts[i] <= t (binary search), clamped so that i + 1 is valid.
  const indexAt = (t, ts = s.track.t) => {
    let lo = 0, hi = ts.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (ts[mid] <= t) lo = mid; else hi = mid;
    }
    return lo;
  };

  const render = () => {
    if (!s.track || !s.layers) return;
    const tr = s.track, t = now(), i = indexAt(t);
    const f = Math.min(Math.max((t - tr.t[i]) / (tr.t[i + 1] - tr.t[i]), 0), 1);
    const lerp = (a) => a[i] + (a[i + 1] - a[i]) * f;
    const pos = [lerp(tr.lat), lerp(tr.lon)];
    s.layers.vehicle.setLatLng(pos);
    s.layers.heading.setLatLngs([pos, [lerp(tr.hlat), lerp(tr.hlon)]]);
    // Trail = samples up to i (appended incrementally) + a short link from sample i to the vehicle.
    if (i < s.trailIdx || s.trailIdx < 0) {
      s.layers.trail.setLatLngs(tr.lat.slice(0, i + 1).map((la, k) => [la, tr.lon[k]]));
    } else {
      for (let k = s.trailIdx + 1; k <= i; k++) s.layers.trail.addLatLng([tr.lat[k], tr.lon[k]]);
    }
    s.trailIdx = i;
    s.layers.link.setLatLngs([[tr.lat[i], tr.lon[i]], pos]);
    // Additional moving markers (e.g. position estimates), each with its own time base.
    for (const x of s.extras) {
      if (!x.layer || x.t.length < 2 || t < x.t[0]) continue;
      const k = indexAt(t, x.t);
      const g = Math.min(Math.max((t - x.t[k]) / (x.t[k + 1] - x.t[k]), 0), 1);
      x.layer.setLatLng([x.lat[k] + (x.lat[k + 1] - x.lat[k]) * g, x.lon[k] + (x.lon[k + 1] - x.lon[k]) * g]);
    }
  };

  const loop = () => {
    render();
    s.raf = s.playing ? requestAnimationFrame(loop) : 0;
  };

  return {
    load(mapElementId, track, ids) {
      s.map = getElement(mapElementId).map;
      s.track = track;
      s.layers = Object.fromEntries(Object.entries(ids).map(([k, id]) => [k, findLayer(id)]));
      s.extras = [];
      s.trailIdx = -1;
      this.sync(0, 1, false);
    },
    // extras: [{id: <layer id>, t: [...], lat: [...], lon: [...]}]; replaces previous extra markers.
    setExtras(extras) {
      s.extras = extras.map((x) => ({ ...x, layer: findLayer(x.id) }));
      render();
    },
    // soft: periodic safety-net re-sync while playing. Both clocks run in real time, so their
    // difference is only network/timer noise; ignore it unless the clocks really drifted apart.
    sync(t, rate, playing, soft = false) {
      if (soft && s.playing && playing && rate === s.rate && Math.abs(t - now()) < Math.max(0.25, 0.1 * rate)) {
        return;
      }
      s.t0 = t;
      s.wall0 = performance.now();
      s.rate = rate;
      s.playing = playing;
      if (s.raf) cancelAnimationFrame(s.raf);
      loop();
    },
    time: now,
  };
})();
