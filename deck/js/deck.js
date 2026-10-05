/* CDN deck: theme switch, slide footers, image slots, Kahoot QR, animated diagrams, Reveal setup.
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

  /* ---- Animated diagrams: <svg class="dg dg-anim" data-loop="8"> on the current slide.
          data-along="#path" data-at="0.3, 5" data-dur="0.6" [data-rev]  a dot that travels that path
          data-show="1 4, 5.7 7.4"                                       visible only in these windows
          <g data-scene="name" data-loop="5">                            drawn while that scene is active:
            the first one by default, then the last visible .fragment[data-scene] on the slide
          Times are seconds within the loop; the loop restarts on every slide or scene change. ---- */
  var dg = { svg: null, scene: null, items: [], t0: 0, raf: 0 };

  function dgList(value) {
    return (value || '').split(',').map(function (part) { return part.trim().split(/\s+/).map(Number); });
  }
  function dgScene(slide, svg) {
    var groups = svg.querySelectorAll('g[data-scene]');
    if (!groups.length) return '';
    var name = groups[0].getAttribute('data-scene');
    slide.querySelectorAll('.fragment.visible[data-scene]').forEach(function (el) {
      name = el.getAttribute('data-scene');
    });
    groups.forEach(function (g) { g.classList.toggle('is-active', g.getAttribute('data-scene') === name); });
    return name;
  }
  function dgTick(now) {
    var t = (now - dg.t0) / 1000;
    dg.items.forEach(function (it) {
      var lt = t % it.loop;
      var on = false;
      if (it.path) {
        it.at.forEach(function (a) {
          var k = (lt - a[0]) / it.dur;
          if (k < 0 || k >= 1) return;
          on = true;
          k = k * k * (3 - 2 * k);                     // ease in and out
          var p = it.path.getPointAtLength(it.len * (it.rev ? 1 - k : k));
          it.el.setAttribute('transform', 'translate(' + p.x.toFixed(1) + ' ' + p.y.toFixed(1) + ')');
        });
      } else {
        on = it.show.some(function (w) { return lt >= w[0] && lt < w[1]; });
      }
      it.el.classList.toggle('is-on', on);
    });
    dg.raf = requestAnimationFrame(dgTick);
  }
  function dgStart() {
    var slide = Reveal.getCurrentSlide();
    var svg = slide && slide.querySelector('.dg-anim');
    var scene = svg ? dgScene(slide, svg) : null;
    if (svg === dg.svg && scene === dg.scene) return;

    cancelAnimationFrame(dg.raf);
    dg.items.forEach(function (it) { it.el.classList.remove('is-on'); });
    dg.svg = svg;
    dg.scene = scene;
    dg.items = [];
    if (!svg) return;

    svg.querySelectorAll('[data-along], [data-show]').forEach(function (el) {
      var group = el.closest('g[data-scene]');
      if (group && !group.classList.contains('is-active')) return;
      var it = { el: el, loop: Number(el.closest('[data-loop]').getAttribute('data-loop')) };
      if (el.hasAttribute('data-along')) {
        it.path = svg.querySelector(el.getAttribute('data-along'));
        it.len = it.path.getTotalLength();
        it.at = dgList(el.getAttribute('data-at'));
        it.dur = Number(el.getAttribute('data-dur'));
        it.rev = el.hasAttribute('data-rev');
      } else {
        it.show = dgList(el.getAttribute('data-show'));
      }
      dg.items.push(it);
    });
    dg.t0 = performance.now();
    dg.raf = requestAnimationFrame(dgTick);
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
      ['slidechanged', 'fragmentshown', 'fragmenthidden'].forEach(function (name) {
        Reveal.on(name, dgStart);
      });
      dgStart();
    });
  }

  window.Deck = { init: init, toggleTheme: toggleTheme, renderQR: renderQR };
})();
