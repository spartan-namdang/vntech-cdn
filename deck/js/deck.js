/* CDN deck: theme switch, slide footers, image slots, Kahoot QR, Reveal setup.
   Loaded in <head> so the saved theme applies before first paint;
   Deck.init() is called at the end of index.html. */
(function () {
  'use strict';

  var THEME_KEY = 'cdn-deck-theme';
  var root = document.documentElement;

  /* ---- Theme: light by default, dark only after the user presses T ---- */
  function readTheme() {
    try { return localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light'; }
    catch (e) { return 'light'; }
  }
  function applyTheme(theme) {
    root.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light');
  }
  function toggleTheme() {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* private mode */ }
  }
  applyTheme(readTheme());
  // keep the speaker view and the main window in step
  window.addEventListener('storage', function (e) {
    if (e.key === THEME_KEY) applyTheme(readTheme());
  });

  /* ---- Footer: section name, taken from data-section on each slide ---- */
  function buildFooters() {
    document.querySelectorAll('.slides > section[data-section]').forEach(function (slide) {
      var foot = document.createElement('footer');
      foot.className = 's-foot';
      foot.textContent = slide.getAttribute('data-section');
      slide.insertBefore(foot, slide.querySelector('aside.notes'));
    });
  }

  /* ---- Image slots: show the dashed placeholder until the file exists ---- */
  function initImageSlots() {
    document.querySelectorAll('.img-slot').forEach(function (slot) {
      var img = slot.querySelector('img');
      if (!img) return;
      function check() { slot.classList.toggle('is-loaded', img.naturalWidth > 0); }
      img.addEventListener('load', check);
      img.addEventListener('error', check);
      if (img.complete) check();
    });
  }

  /* ---- Kahoot QR: link and PIN come from data-kahoot-url / data-kahoot-pin
          on the Kahoot <section> in index.html ---- */
  function cssVar(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }
  function renderQR(url, pin) {
    var panel = document.querySelector('.qr-panel');
    var pinEl = document.querySelector('.qr-pin');
    if (!panel || !pinEl) return;
    var canvas = panel.querySelector('canvas');

    url = (url || '').trim();
    pin = (pin || '').trim();

    pinEl.classList.toggle('is-empty', !pin);
    // Kahoot shows PINs as "123 456" or "123 4567"
    pinEl.textContent = pin ? pin.replace(/^(\d{3})(\d{3,4})$/, '$1 $2') : 'PIN shown on the day';

    if (!url || typeof qrcode !== 'function') {
      panel.classList.add('is-empty');
      panel.classList.remove('is-ready');
      return;
    }

    var qr = qrcode(0, 'M');
    qr.addData(url);
    qr.make();
    var count = qr.getModuleCount();
    var quiet = 4;                                   // quiet zone, in modules
    var cell = Math.max(4, Math.floor(1200 / (count + quiet * 2)));
    var size = cell * (count + quiet * 2);
    canvas.width = size;
    canvas.height = size;
    var ctx = canvas.getContext('2d');
    ctx.fillStyle = cssVar('--qr-bg');
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = cssVar('--qr-fg');
    for (var r = 0; r < count; r++) {
      for (var c = 0; c < count; c++) {
        if (qr.isDark(r, c)) ctx.fillRect((c + quiet) * cell, (r + quiet) * cell, cell, cell);
      }
    }
    panel.classList.remove('is-empty');
    panel.classList.add('is-ready');
  }
  function initQR() {
    var slide = document.querySelector('section[data-kahoot-url]');
    if (!slide) return;
    renderQR(slide.getAttribute('data-kahoot-url'), slide.getAttribute('data-kahoot-pin'));
  }

  /* ---- Reveal ---- */
  function init() {
    buildFooters();
    initImageSlots();
    initQR();

    return Reveal.initialize({
      width: 1280,
      height: 720,
      margin: 0,
      minScale: 0.2,
      maxScale: 2.5,
      hash: true,
      center: false,
      display: 'flex',
      slideNumber: 'c/t',
      progress: true,
      controls: false,
      transition: 'fade',
      transitionSpeed: 'fast',
      backgroundTransition: 'none',
      plugins: [RevealNotes, RevealHighlight]
    }).then(function () {
      Reveal.addKeyBinding(
        { keyCode: 84, key: 'T', description: 'Toggle light / dark theme' },
        toggleTheme
      );
    });
  }

  window.Deck = { init: init, toggleTheme: toggleTheme, renderQR: renderQR };
})();
