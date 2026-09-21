(function () {
  "use strict";
  var d = document.documentElement;

  function save(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }

  function applyLang(lang) {
    d.setAttribute("data-lang", lang);
    d.lang = lang === "pt" ? "pt-BR" : "en";
    document.title = d.getAttribute("data-title-" + lang);
    var meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute("content", d.getAttribute("data-desc-" + lang));
    document.querySelectorAll("[data-set-lang]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-set-lang") === lang));
    });
    document.querySelectorAll("[data-label-" + lang + "]").forEach(function (el) {
      el.setAttribute("aria-label", el.getAttribute("data-label-" + lang));
    });
    document.querySelectorAll("video").forEach(function (v) {
      Array.prototype.forEach.call(v.textTracks, function (t) {
        t.mode = (t.language.indexOf(lang) === 0) ? "showing" : "disabled";
      });
    });
  }

  document.querySelectorAll("[data-set-lang]").forEach(function (b) {
    b.addEventListener("click", function () {
      var lang = b.getAttribute("data-set-lang");
      save("tv-lang", lang);
      applyLang(lang);
    });
  });
  applyLang(d.getAttribute("data-lang") || "en");

  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) toggle.addEventListener("click", function () {
    var current = d.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = current === "dark" ? "light" : "dark";
    d.setAttribute("data-theme", next);
    save("tv-theme", next);
  });

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var code = btn.parentElement.querySelector("pre code");
      copyText(code.textContent).then(function () {
        btn.classList.add("ok");
        var original = btn.innerHTML;
        btn.innerHTML = '<span data-l="en">Copied</span><span data-l="pt">Copiado</span>';
        setTimeout(function () { btn.classList.remove("ok"); btn.innerHTML = original; }, 1600);
      });
    });
  });

  document.querySelectorAll(".tabs").forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role="tab"]'));
    function select(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
      });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (e) {
        var k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!k) return;
        var next = tabs[(i + k + tabs.length) % tabs.length];
        select(next); next.focus(); e.preventDefault();
      });
    });
    if (/Win/.test(navigator.platform || navigator.userAgent)) select(tabs[tabs.length - 1]);
  });
})();
