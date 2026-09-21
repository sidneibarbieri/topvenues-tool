(function () {
  var d = document.documentElement, store = null, lang = null, theme = null;
  try { store = window.localStorage; } catch (e) {}
  var q = (new URLSearchParams(location.search).get("lang") || "").toLowerCase();
  if (q.indexOf("pt") === 0) lang = "pt"; else if (q.indexOf("en") === 0) lang = "en";
  if (!lang) { try { lang = store && store.getItem("tv-lang"); } catch (e) {} }
  if (lang !== "en" && lang !== "pt") lang = (navigator.language || "en").toLowerCase().indexOf("pt") === 0 ? "pt" : "en";
  d.setAttribute("data-lang", lang);
  d.lang = lang === "pt" ? "pt-BR" : "en";
  try { theme = store && store.getItem("tv-theme"); } catch (e) {}
  if (theme === "light" || theme === "dark") d.setAttribute("data-theme", theme);
})();
