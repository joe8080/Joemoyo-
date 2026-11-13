/* Joe — page behaviour. You shouldn't need to edit this file; content lives in content.js. */
(function () {
  "use strict";

  var C = window.SITE_CONTENT || {};
  var root = document.documentElement;
  var EDIT = /(?:^|[?&])edit(?:=|&|$)/.test(location.search.slice(1)) || location.hash === "#edit";

  /* ── Reading content ──────────────────────────────────────── */
  function get(path) {
    return path.split(".").reduce(function (o, k) { return o == null ? undefined : o[k]; }, C);
  }
  function raw(path) {
    var v = get(path);
    if (v == null) return "";
    v = String(v).trim();
    return /^\[[^\]]*\]$/.test(v) ? "" : v; // "[PLACEHOLDER]" counts as empty
  }
  function safeUrl(u) {
    if (!u) return "";
    try {
      var url = new URL(u, location.href);
      return /^(https?:|mailto:)$/.test(url.protocol) ? url.href : "";
    } catch (e) { return ""; }
  }
  function youtubeId(u) {
    if (!u) return "";
    var m = u.match(/(?:youtube(?:-nocookie)?\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/|live\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    return m ? m[1] : "";
  }
  var EMAIL_RE = /^[^\s@<>"']+@[^\s@<>"']+\.[^\s@<>"']{2,}$/;

  var validators = {
    youtubeChannelUrl: function (v) { return /^https:\/\/(www\.|m\.)?youtube\.com\//.test(safeUrl(v)); },
    introVideoUrl: function (v) { return !!youtubeId(v); },
    publicContactEmail: function (v) { return EMAIL_RE.test(v); },
    "currentProject.videoUrl": function (v) { return !!safeUrl(v); },
  };

  /** true when a content value is filled in and looks valid */
  function ok(path) {
    var v = raw(path);
    if (!v) return false;
    var check = validators[path] || (/(photos\.|\.image$|Thumbnail$)/.test(path) ? function (x) { return !!safeUrl(x); } : null);
    return check ? check(v) : true;
  }
  function why(path) {
    return raw(path) ? path + " (doesn't look right — check the link)" : path;
  }

  /* ── Fill text, links and images ──────────────────────────── */
  document.querySelectorAll("[data-text]").forEach(function (el) {
    var p = el.getAttribute("data-text");
    if (ok(p)) el.textContent = raw(p);
  });

  document.querySelectorAll("[data-link]").forEach(function (el) {
    var p = el.getAttribute("data-link");
    if (ok(p)) el.href = safeUrl(raw(p));
  });

  document.querySelectorAll("[data-mailto]").forEach(function (el) {
    var p = el.getAttribute("data-mailto");
    if (!ok(p)) return;
    var subject = raw("emailSubject");
    el.href = "mailto:" + raw(p) + (subject ? "?subject=" + encodeURIComponent(subject) : "");
  });

  document.querySelectorAll("img[data-src]").forEach(function (img) {
    var p = img.getAttribute("data-src");
    if (!ok(p)) return;
    img.src = safeUrl(raw(p));
    var a = img.getAttribute("data-alt");
    img.alt = a ? raw(a) : "";
  });

  /* ── Show / hide pieces depending on what's been supplied ── */
  var missing = []; // for the editor panel

  document.querySelectorAll("[data-requires], [data-fallback-for]").forEach(function (el) {
    var req = (el.getAttribute("data-requires") || "").split(/\s+/).filter(Boolean);
    var fb = (el.getAttribute("data-fallback-for") || "").split(/\s+/).filter(Boolean);
    var lacking = req.filter(function (p) { return !ok(p); });
    var replaced = fb.some(ok);
    var show = lacking.length === 0 && !replaced;
    el.hidden = !show;

    // Editor view: reveal unfinished elements with a clear "Missing" label.
    if (EDIT && !show && lacking.length && !fb.length && !el.hasAttribute("data-optional")) {
      el.hidden = false;
      el.setAttribute("data-missing", lacking.map(why).join(" + "));
      el.removeAttribute("href");
      if (el.tagName === "BUTTON") el.disabled = true;
      lacking.forEach(function (p) { if (missing.indexOf(p) < 0) missing.push(p); });
    }
  });

  /* ── Social links ─────────────────────────────────────────── */
  var SOCIAL_LABELS = {
    instagram: "Instagram", tiktok: "TikTok", x: "X", threads: "Threads", linkedin: "LinkedIn",
    soundcloud: "SoundCloud", spotify: "Spotify", bandcamp: "Bandcamp",
  };
  var socialList = document.querySelector(".socials");
  if (socialList && C.socials) {
    Object.keys(C.socials).forEach(function (key) {
      var url = safeUrl(raw("socials." + key));
      if (!url || !/^https:/.test(url)) return;
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "me noopener";
      a.textContent = SOCIAL_LABELS[key] || key;
      li.appendChild(a);
      socialList.appendChild(li);
    });
    socialList.hidden = !socialList.children.length;
  }

  /* ── Intro video: lightweight thumbnail until tapped ─────── */
  var facade = document.querySelector(".video__facade");
  var vid = youtubeId(raw("introVideoUrl"));
  if (facade && vid) {
    var thumb = facade.querySelector(".video__thumb");
    if (ok("introVideoThumbnail")) {
      thumb.src = safeUrl(raw("introVideoThumbnail"));
    } else {
      thumb.src = "https://i.ytimg.com/vi/" + vid + "/maxresdefault.jpg";
      thumb.addEventListener("load", function onLoad() {
        // YouTube serves a tiny grey image when no HD thumbnail exists
        if (thumb.naturalWidth && thumb.naturalWidth < 200) {
          thumb.removeEventListener("load", onLoad);
          thumb.src = "https://i.ytimg.com/vi/" + vid + "/hqdefault.jpg";
        }
      });
    }
    facade.addEventListener("click", function () {
      var iframe = document.createElement("iframe");
      iframe.src = "https://www.youtube-nocookie.com/embed/" + vid + "?autoplay=1&rel=0&playsinline=1";
      iframe.title = raw("introVideoTitle") || "Intro video";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      facade.replaceWith(iframe);
      iframe.focus();
    });
  }

  /* ── Navigation ───────────────────────────────────────────── */
  var nav = document.querySelector(".nav");
  var toggle = document.querySelector(".nav__toggle");
  function setMenu(open) {
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  }
  if (toggle) {
    toggle.addEventListener("click", function () { setMenu(!nav.classList.contains("is-open")); });
    document.querySelectorAll(".nav__links a").forEach(function (a) {
      a.addEventListener("click", function () { setMenu(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) { setMenu(false); toggle.focus(); }
    });
  }
  var onScroll = function () { nav.classList.toggle("is-scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ── Gentle scroll reveal (skipped when reduced motion is on) */
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce && "IntersectionObserver" in window) {
    root.classList.add("motion");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  }

  /* ── Footer year ──────────────────────────────────────────── */
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ── Editor checklist (only with ?edit) ───────────────────── */
  if (!EDIT) return;
  root.classList.add("is-edit");

  var items = [
    { label: "YouTube channel link", key: "youtubeChannelUrl", need: true },
    { label: "Intro video link", key: "introVideoUrl", need: true },
    { label: "Public collaboration email", key: "publicContactEmail", need: true },
    { label: "Portrait or studio photo", key: "photos.portrait", note: "optional — a typography panel shows until then" },
    { label: "Second studio photo (About)", key: "photos.studio", note: "optional" },
    { label: "Current project", keys: ["currentProject.title", "currentProject.description"], note: "optional — hidden until title and description are filled in" },
    { label: "Social links", social: true, note: "optional — each one appears when you paste a link" },
  ];

  var panel = document.createElement("aside");
  panel.className = "editor-panel";
  panel.setAttribute("aria-label", "Editor checklist");

  var todo = items.filter(function (i) { return i.need && !ok(i.key); }).length;

  var head = document.createElement("header");
  var title = document.createElement("strong");
  title.textContent = todo ? "Editor view · " + todo + " to finish" : "Editor view · essentials done";
  var btns = document.createElement("span");
  var pub = document.createElement("a");
  pub.href = location.pathname;
  pub.textContent = "Public view";
  var hide = document.createElement("button");
  hide.type = "button";
  hide.textContent = "Hide";
  hide.addEventListener("click", function () {
    panel.classList.toggle("is-collapsed");
    hide.textContent = panel.classList.contains("is-collapsed") ? "Show" : "Hide";
  });
  btns.appendChild(pub);
  btns.appendChild(document.createTextNode(" "));
  btns.appendChild(hide);
  head.appendChild(title);
  head.appendChild(btns);

  var body = document.createElement("div");
  body.className = "ep-body";
  var intro = document.createElement("p");
  intro.textContent = "Only you see this. Edit content.js, save, then refresh. Orange dashed boxes are hidden from visitors until they're filled in.";
  body.appendChild(intro);

  var ol = document.createElement("ol");
  items.forEach(function (i) {
    var done = i.social
      ? Object.keys(C.socials || {}).some(function (k) { return !!safeUrl(raw("socials." + k)); })
      : (i.keys || [i.key]).every(ok);
    var li = document.createElement("li");
    var mark = document.createElement("span");
    mark.className = done ? "ok" : "";
    mark.textContent = done ? "✓ " : "○ ";
    li.appendChild(mark);
    li.appendChild(document.createTextNode(i.label + " "));
    var code = document.createElement("code");
    code.textContent = i.social ? "socials" : (i.keys || [i.key]).join(" + ");
    li.appendChild(code);
    if (i.note && !done) {
      li.appendChild(document.createTextNode(" — " + i.note));
    } else if (!done && raw(i.key)) {
      li.appendChild(document.createTextNode(" — filled in, but doesn't look valid"));
    }
    ol.appendChild(li);
  });
  var launch = document.createElement("li");
  launch.textContent = "On launch day: delete the robots “noindex” line in index.html and set og:image to the full web address.";
  ol.appendChild(launch);
  body.appendChild(ol);

  panel.appendChild(head);
  panel.appendChild(body);
  document.body.appendChild(panel);

  // Tapping a missing element in editor view points you to the checklist.
  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-missing]");
    if (!el) return;
    e.preventDefault();
    panel.classList.remove("is-collapsed");
    hide.textContent = "Hide";
    panel.animate && panel.animate([{ transform: "scale(1)" }, { transform: "scale(1.03)" }, { transform: "scale(1)" }], { duration: 350 });
  });

  if (window.console) console.info("[Joe site] Missing content:", missing.length ? missing.join(", ") : "none");
})();
