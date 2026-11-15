/* ==================================================================
   Global Wargame — theme.js
   Light/dark theme switcher with localStorage persistence and a
   floating toggle button injected into every page.
   ================================================================== */
(function () {
  'use strict';

  var KEY = 'gw-theme';
  var DEFAULT = 'light';

  function getStored() {
    try { return localStorage.getItem(KEY); } catch (_) { return null; }
  }
  function setStored(v) {
    try { localStorage.setItem(KEY, v); } catch (_) {}
  }
  function applyTheme(theme) {
    var t = (theme === 'dark') ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', t);
    document.documentElement.style.colorScheme = t;
    return t;
  }
  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || DEFAULT;
  }
  function toggleTheme() {
    var next = currentTheme() === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    setStored(next);
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: next } }));
  }

  // Apply immediately to avoid flash-of-wrong-theme.
  applyTheme(getStored() || DEFAULT);

  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else { fn(); }
  }

  function ensureBackdrop() {
    if (document.querySelector('.gw-bg')) return;
    var bg = document.createElement('div');
    bg.className = 'gw-bg';
    if (document.body && document.body.classList.contains('with-grid')) {
      bg.classList.add('with-grid');
    }
    bg.setAttribute('aria-hidden', 'true');
    if (document.body.firstChild) {
      document.body.insertBefore(bg, document.body.firstChild);
    } else {
      document.body.appendChild(bg);
    }
  }

  function buildToggle() {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'theme-toggle';
    btn.setAttribute('aria-label', 'Toggle color theme');
    btn.setAttribute('title', 'Toggle theme');
    btn.innerHTML =
      '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>' +
      '</svg>' +
      '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<circle cx="12" cy="12" r="4"/>' +
        '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>' +
      '</svg>';
    btn.addEventListener('click', toggleTheme);
    return btn;
  }

  ready(function () {
    ensureBackdrop();

    var existing = document.querySelector('[data-theme-toggle]');
    if (existing) {
      existing.addEventListener('click', toggleTheme);
    } else if (!document.querySelector('.theme-toggle')) {
      document.body.appendChild(buildToggle());
    }

    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        document.documentElement.classList.add('theme-ready');
      });
    });
  });

  window.GWTheme = {
    get:    currentTheme,
    set:    function (t) { applyTheme(t); setStored(t); },
    toggle: toggleTheme
  };
})();

/* ==================================================================
   App shell integration
   home.html is the single entry point. It hosts every tool in an
   iframe pane. This block:
     - sends a top-level visit to any tool page into the shell
       (opt out with ?standalone=1, or when opened as a popup),
     - marks embedded pages with html.gw-embedded so they can hide
       their own back links and theme toggle,
     - turns links between tools into tab switches in the shell,
     - keeps the theme in step with the shell.
   ================================================================== */
(function () {
  'use strict';

  var FILES = {
    'home.html': 'home', 'overview.html': 'home', 'index.html': 'cards',
    'engine.html': 'play', 'globe.html': 'globe', 'tactical.html': 'tactical',
    'card-builder.html': 'builder', 'diagnostics.html': 'diagnostics'
  };

  function locate(href) {
    var u;
    try { u = new URL(href, location.href); } catch (_) { return null; }
    var parts = u.pathname.split('/');
    var file = parts.pop();
    var dir = parts.pop();
    if (dir === 'cards' && /\.html?$/i.test(file)) {
      return { route: 'cards', path: 'cards/' + file, url: u };
    }
    if (!file) file = 'index.html';
    if (FILES[file]) return { route: FILES[file], path: file, url: u, file: file };
    return null;
  }

  function sameOrigin(u) {
    if (location.protocol === 'file:') return u.protocol === 'file:';
    return u.origin === location.origin;
  }
  function postTarget() {
    if (location.protocol === 'file:' || !location.origin || location.origin === 'null') return '*';
    return location.origin;
  }
  function fromParent(e) {
    if (e.source !== window.parent) return false;
    if (location.protocol === 'file:' || !location.origin || location.origin === 'null') {
      return e.origin === 'null' || e.origin === 'file://';
    }
    return e.origin === location.origin;
  }

  var here = locate(location.href);
  var embedded = window.self !== window.top;
  var standalone = /(^|[?&])standalone=1(&|$)/.test(location.search) ||
                   window.name === 'wargame-globe' || !!window.opener;
  var shellHref = (here && here.route === 'cards' && here.path.indexOf('cards/') === 0)
                  ? '../home.html' : 'home.html';

  // 1. Top-level visit to a tool page: open it inside the shell instead.
  if (!embedded && !standalone && here && here.file !== 'home.html') {
    var rootVisit = /\/$/.test(location.pathname);
    var target = rootVisit ? 'home.html'
      : shellHref + '#' + (here.route === 'cards' && here.path !== 'index.html' ? here.path : here.route);
    location.replace(target);
    return;
  }

  function nav(route, path) {
    if (embedded) {
      try { window.parent.postMessage({ type: 'gw-nav', route: route, path: path || null }, postTarget()); } catch (_) {}
      return;
    }
    var inv = {};
    for (var f in FILES) if (!(f in inv)) inv[FILES[f]] = f;
    location.href = path || inv[route] || 'home.html';
  }
  if (window.GWTheme) window.GWTheme.nav = nav;

  if (!embedded) return;

  // 2. Embedded inside the shell.
  document.documentElement.classList.add('gw-embedded');

  function apply(t) {
    if (window.GWTheme && window.GWTheme.get() !== t) {
      document.documentElement.setAttribute('data-theme', t === 'dark' ? 'dark' : 'light');
      document.documentElement.style.colorScheme = t === 'dark' ? 'dark' : 'light';
      document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: t } }));
    }
  }
  window.addEventListener('message', function (e) {
    if (!fromParent(e)) return;
    var d = e.data;
    if (d && d.type === 'gw-theme') apply(d.theme);
  });
  window.addEventListener('storage', function (e) {
    if (e.key === 'gw-theme' && e.newValue) apply(e.newValue);
  });

  // Links to another tool switch tabs in the shell. Links within the same
  // tool (a card back to the catalogue) navigate inside the pane as before.
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || a.hasAttribute('download')) return;
    var raw = a.getAttribute('href');
    if (!raw || raw.charAt(0) === '#' || /^(javascript|mailto|blob|data):/i.test(raw)) return;
    var dest = locate(a.href);
    if (!dest || !sameOrigin(dest.url)) return;
    if (here && dest.route === here.route) {
      if (a.target === '_blank') { e.preventDefault(); location.href = a.href; }
      return;
    }
    e.preventDefault();
    nav(dest.route, dest.route === 'cards' && dest.path !== 'index.html' ? dest.path : null);
  }, true);

  // Tell the shell where this pane is, so the address bar can deep-link it.
  try {
    window.parent.postMessage({ type: 'gw-loc', route: here ? here.route : null, path: here ? here.path : null }, postTarget());
  } catch (_) {}
})();
