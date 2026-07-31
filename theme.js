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
