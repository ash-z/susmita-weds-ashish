/* Song Clip Maker: everything runs in the browser, the song is never uploaded. */
(function () {
  'use strict';

  var OUTPUT_RATE = 44100;   // MP3 sample rate for every clip
  var FADE_SECONDS = 1.5;
  var MIN_CLIP = 0.5;
  var DEFAULT_CLIP = 30;

  var $ = function (id) { return document.getElementById(id); };
  var els = {
    drop: $('drop'), file: $('file'), dropText: $('drop-text'), editor: $('editor'),
    songName: $('song-name'), wrap: document.querySelector('.wave-wrap'), wave: $('wave'),
    hStart: $('h-start'), hEnd: $('h-end'), playhead: $('playhead'),
    start: $('start'), end: $('end'), length: $('length'),
    play: $('play'), fade: $('fade'), bitrate: $('bitrate'), mono: $('mono'),
    exportBtn: $('export'), progress: $('progress'), status: $('status'),
    result: $('result'), resultAudio: $('result-audio'), download: $('download'), share: $('share')
  };

  var ctx = null;
  var buffer = null;
  var songBase = 'song';
  var sel = { start: 0, end: 0 };
  var peaks = null;
  var playing = null;   // { source, startedAt, from, to }
  var clipFile = null;
  var clipUrl = null;

  function audioCtx() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    return ctx;
  }

  // ---------- time helpers ----------

  function fmt(sec) {
    var m = Math.floor(sec / 60);
    var s = sec - m * 60;
    return m + ':' + (s < 10 ? '0' : '') + s.toFixed(1);
  }

  function parseTime(text) {
    var parts = String(text).trim().split(':');
    if (parts.length > 2) return NaN;
    var secs = parts.length === 2 ? Number(parts[0]) * 60 + Number(parts[1]) : Number(parts[0]);
    return parts.some(function (p) { return p === ''; }) ? NaN : secs;
  }

  // ---------- loading ----------

  function loadFile(file) {
    if (!file) return;
    stopPreview();
    setStatus('Reading ' + file.name + '…');
    songBase = file.name.replace(/\.[^.]+$/, '').replace(/[^\w\- ]+/g, '').trim() || 'song';
    file.arrayBuffer().then(function (data) {
      return new Promise(function (resolve, reject) {
        // callback form for older Safari
        audioCtx().decodeAudioData(data, resolve, reject);
      });
    }).then(function (decoded) {
      buffer = decoded;
      sel.start = 0;
      sel.end = Math.min(DEFAULT_CLIP, buffer.duration);
      els.songName.textContent = file.name + ' · ' + fmt(buffer.duration);
      els.dropText.textContent = 'Choose a different song';
      els.editor.hidden = false;
      els.result.hidden = true;
      computePeaks();
      render();
      setStatus('Drag the pink handles or type times to pick your clip.');
    }).catch(function () {
      setStatus('Sorry, this browser could not read that file. Try an MP3, M4A or WAV.');
    });
  }

  els.file.addEventListener('change', function () { loadFile(els.file.files[0]); });
  ['dragenter', 'dragover'].forEach(function (t) {
    els.drop.addEventListener(t, function (e) { e.preventDefault(); els.drop.classList.add('over'); });
  });
  ['dragleave', 'drop'].forEach(function (t) {
    els.drop.addEventListener(t, function (e) { e.preventDefault(); els.drop.classList.remove('over'); });
  });
  els.drop.addEventListener('drop', function (e) {
    loadFile(e.dataTransfer.files && e.dataTransfer.files[0]);
  });

  // ---------- waveform ----------

  function computePeaks() {
    var width = Math.max(200, els.wrap.clientWidth);
    var per = Math.max(1, Math.floor(buffer.length / width));
    var chans = [];
    for (var c = 0; c < buffer.numberOfChannels; c++) chans.push(buffer.getChannelData(c));
    peaks = new Float32Array(width);
    for (var x = 0; x < width; x++) {
      var max = 0;
      var from = x * per;
      var to = Math.min(buffer.length, from + per);
      // stride keeps this fast for long songs
      var step = Math.max(1, Math.floor(per / 200));
      for (var i = from; i < to; i += step) {
        for (var k = 0; k < chans.length; k++) {
          var v = Math.abs(chans[k][i]);
          if (v > max) max = v;
        }
      }
      peaks[x] = max;
    }
  }

  function render() {
    if (!buffer) return;
    var dpr = window.devicePixelRatio || 1;
    var w = els.wrap.clientWidth;
    var h = els.wrap.clientHeight;
    var canvas = els.wave;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    var g = canvas.getContext('2d');
    g.scale(dpr, dpr);
    g.clearRect(0, 0, w, h);

    var sx = sel.start / buffer.duration * w;
    var ex = sel.end / buffer.duration * w;
    g.fillStyle = 'rgba(176, 58, 98, 0.10)';
    g.fillRect(sx, 0, ex - sx, h);

    var mid = h / 2;
    for (var x = 0; x < w; x++) {
      var p = peaks[Math.floor(x / w * peaks.length)] || 0;
      var bar = Math.max(1, p * (h - 10));
      g.fillStyle = x >= sx && x <= ex ? '#b03a62' : '#d9c6cd';
      g.fillRect(x, mid - bar / 2, 1, bar);
    }

    els.hStart.style.left = sx + 'px';
    els.hEnd.style.left = ex + 'px';
    els.start.value = fmt(sel.start);
    els.end.value = fmt(sel.end);
    els.length.textContent = 'Clip length ' + fmt(sel.end - sel.start);
  }

  window.addEventListener('resize', function () {
    if (!buffer) return;
    computePeaks();
    render();
  });

  // ---------- selecting ----------

  function setEdge(which, t) {
    t = Math.max(0, Math.min(buffer.duration, t));
    if (which === 'start') sel.start = Math.min(t, sel.end - MIN_CLIP);
    else sel.end = Math.max(t, sel.start + MIN_CLIP);
    sel.start = Math.max(0, sel.start);
    sel.end = Math.min(buffer.duration, sel.end);
    els.result.hidden = true;
    render();
  }

  function timeAt(clientX) {
    var r = els.wrap.getBoundingClientRect();
    return (clientX - r.left) / r.width * buffer.duration;
  }

  var dragging = null;
  els.wrap.addEventListener('pointerdown', function (e) {
    if (!buffer) return;
    var t = timeAt(e.clientX);
    if (e.target === els.hStart) dragging = 'start';
    else if (e.target === els.hEnd) dragging = 'end';
    else dragging = Math.abs(t - sel.start) < Math.abs(t - sel.end) ? 'start' : 'end';
    stopPreview();
    els.wrap.setPointerCapture(e.pointerId);
    setEdge(dragging, t);
  });
  els.wrap.addEventListener('pointermove', function (e) {
    if (dragging) setEdge(dragging, timeAt(e.clientX));
  });
  ['pointerup', 'pointercancel'].forEach(function (t) {
    els.wrap.addEventListener(t, function () { dragging = null; });
  });

  [['start', els.start], ['end', els.end]].forEach(function (pair) {
    pair[1].addEventListener('change', function () {
      var t = parseTime(pair[1].value);
      if (isNaN(t)) { render(); return; }
      stopPreview();
      setEdge(pair[0], t);
    });
  });

  // ---------- preview ----------

  function applyFades(gain, at, dur) {
    if (!els.fade.checked) return;
    var f = Math.min(FADE_SECONDS, dur / 3);
    gain.setValueAtTime(0, at);
    gain.linearRampToValueAtTime(1, at + f);
    gain.setValueAtTime(1, at + dur - f);
    gain.linearRampToValueAtTime(0, at + dur);
  }

  function startPreview() {
    var ac = audioCtx();
    if (ac.state === 'suspended') ac.resume();
    var dur = sel.end - sel.start;
    var src = ac.createBufferSource();
    var gain = ac.createGain();
    src.buffer = buffer;
    src.connect(gain).connect(ac.destination);
    applyFades(gain.gain, ac.currentTime, dur);
    src.start(ac.currentTime, sel.start, dur);
    playing = { source: src, startedAt: ac.currentTime, from: sel.start, to: sel.end };
    src.onended = function () { if (playing && playing.source === src) stopPreview(); };
    els.play.textContent = '■ Stop';
    els.playhead.style.display = 'block';
    requestAnimationFrame(tick);
  }

  function stopPreview() {
    if (!playing) return;
    var src = playing.source;
    playing = null;
    try { src.stop(); } catch (e) { /* already stopped */ }
    els.play.textContent = '▶ Preview';
    els.playhead.style.display = 'none';
  }

  function tick() {
    if (!playing) return;
    var t = playing.from + (audioCtx().currentTime - playing.startedAt);
    els.playhead.style.left = (Math.min(t, playing.to) / buffer.duration * els.wrap.clientWidth) + 'px';
    requestAnimationFrame(tick);
  }

  els.play.addEventListener('click', function () {
    if (playing) stopPreview(); else startPreview();
  });

  // ---------- export ----------

  function renderClip(channels) {
    var dur = sel.end - sel.start;
    var Offline = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    // rendering offline resamples to 44.1 kHz, downmixes and applies the fades in one pass
    var off = new Offline(channels, Math.ceil(dur * OUTPUT_RATE), OUTPUT_RATE);
    var src = off.createBufferSource();
    var gain = off.createGain();
    src.buffer = buffer;
    src.connect(gain).connect(off.destination);
    applyFades(gain.gain, 0, dur);
    src.start(0, sel.start, dur);
    return off.startRendering();
  }

  function toInt16(f32) {
    var out = new Int16Array(f32.length);
    for (var i = 0; i < f32.length; i++) {
      var s = Math.max(-1, Math.min(1, f32[i]));
      out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return out;
  }

  function encodeMp3(rendered, kbps) {
    var channels = rendered.numberOfChannels;
    var left = toInt16(rendered.getChannelData(0));
    var right = channels > 1 ? toInt16(rendered.getChannelData(1)) : null;
    var encoder = new lamejs.Mp3Encoder(channels, OUTPUT_RATE, kbps);
    var FRAME = 1152;
    var parts = [];
    var i = 0;

    return new Promise(function (resolve) {
      function chunk() {
        // encode a slice, then yield so the progress bar can update
        var stop = Math.min(left.length, i + FRAME * 200);
        for (; i < stop; i += FRAME) {
          var l = left.subarray(i, i + FRAME);
          var buf = right ? encoder.encodeBuffer(l, right.subarray(i, i + FRAME)) : encoder.encodeBuffer(l);
          if (buf.length) parts.push(new Uint8Array(buf));
        }
        els.progress.value = 0.2 + 0.8 * (i / left.length);
        if (i < left.length) { setTimeout(chunk, 0); return; }
        var tail = encoder.flush();
        if (tail.length) parts.push(new Uint8Array(tail));
        resolve(new Blob(parts, { type: 'audio/mpeg' }));
      }
      chunk();
    });
  }

  els.exportBtn.addEventListener('click', function () {
    if (!buffer) return;
    stopPreview();
    var channels = els.mono.checked || buffer.numberOfChannels === 1 ? 1 : 2;
    var kbps = Number(els.bitrate.value);
    els.exportBtn.disabled = true;
    els.result.hidden = true;
    els.progress.hidden = false;
    els.progress.value = 0.05;
    setStatus('Cutting your clip…');

    renderClip(channels).then(function (rendered) {
      els.progress.value = 0.2;
      setStatus('Encoding MP3…');
      return encodeMp3(rendered, kbps);
    }).then(function (blob) {
      var name = songBase + ' clip ' + fmt(sel.start).replace(/[:.]/g, '-') + '.mp3';
      clipFile = new File([blob], name, { type: 'audio/mpeg' });
      if (clipUrl) URL.revokeObjectURL(clipUrl);
      clipUrl = URL.createObjectURL(blob);
      els.resultAudio.src = clipUrl;
      els.download.href = clipUrl;
      els.download.download = name;
      els.share.hidden = !(navigator.canShare && navigator.canShare({ files: [clipFile] }));
      els.result.hidden = false;
      setStatus('Done! ' + name + ' · ' + (blob.size / 1048576).toFixed(2) + ' MB');
    }).catch(function (err) {
      setStatus('Could not make the clip: ' + (err && err.message ? err.message : err));
    }).then(function () {
      els.exportBtn.disabled = false;
      els.progress.hidden = true;
    });
  });

  els.share.addEventListener('click', function () {
    if (!clipFile) return;
    navigator.share({ files: [clipFile], title: clipFile.name }).catch(function (err) {
      if (err && err.name !== 'AbortError') setStatus('Sharing failed, use Download instead.');
    });
  });

  function setStatus(text) { els.status.textContent = text; }
})();
