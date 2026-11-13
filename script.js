/* ============================================================
   Abdul Manan — portfolio  ·  interactions, theme, live GitHub stats
   ------------------------------------------------------------
   Projects and blog posts are static HTML written by tools/build.py.
   This file only adds motion, the theme toggle, the live GitHub
   numbers and the contact form.
   ============================================================ */
(() => {
  "use strict";

  const GH_USER = "abdulmanan69";

  /* ------------------------------------------------------------
     CONTACT — where messages land. All of these are free forever.
       endpoint : FormSubmit. Swap the address for the random alias
                  FormSubmit gives you after activation, so the raw
                  inbox never sits in the HTML for scrapers.
       whatsapp : digits only, country code first — "923001234567".
       telegram : username without the @.
       discord  : a channel webhook URL (optional mirror; the form
                  also pings it so a message is never only in email).
     Leave a value as "" and that button simply isn't rendered.
     ------------------------------------------------------------ */
  const CONTACT = {
    email:    "manan999999999@gmail.com",
    endpoint: "https://formsubmit.co/ajax/manan999999999@gmail.com",
    whatsapp: "",
    telegram: "",
    discord:  ""
  };

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canHover = matchMedia("(hover: hover)").matches;
  const $  = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];

  $("#year").textContent = new Date().getFullYear();

  /* ---------- loader ---------- */
  const loader = $("#loader");
  addEventListener("load", () => setTimeout(() => loader.classList.add("done"), 900));
  setTimeout(() => loader.classList.add("done"), 2600); // safety

  /* ---------- theme toggle ---------- */
  const root = document.documentElement;
  const saved = localStorage.getItem("theme");
  const prefersDark = matchMedia("(prefers-color-scheme: dark)").matches;
  root.setAttribute("data-theme", saved || (prefersDark ? "dark" : "light"));
  $("#themeToggle").addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    $('meta[name="theme-color"]').setAttribute("content", next === "dark" ? "#131219" : "#faf8f5");
  });

  /* ---------- custom cursor ---------- */
  const dot = $("[data-cursor-dot]"), ring = $("[data-cursor-ring]");
  if (dot && ring && canHover) {
    let mx = innerWidth / 2, my = innerHeight / 2, rx = mx, ry = my;
    addEventListener("mousemove", e => {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = `translate(${mx}px,${my}px) translate(-50%,-50%)`;
    });
    (function loop() {
      rx += (mx - rx) * .18; ry += (my - ry) * .18;
      ring.style.transform = `translate(${rx}px,${ry}px) translate(-50%,-50%)`;
      requestAnimationFrame(loop);
    })();
    const bind = () => $$("[data-hover], a, button").forEach(el => {
      el.addEventListener("mouseenter", () => ring.classList.add("is-hover"));
      el.addEventListener("mouseleave", () => ring.classList.remove("is-hover"));
    });
    bind();
    window.__rebindCursor = bind;
  }

  /* ---------- nav + progress ---------- */
  const nav = $("#nav"), prog = $("#scrollProgress");
  const onScroll = () => {
    nav.classList.toggle("scrolled", scrollY > 30);
    const h = document.documentElement.scrollHeight - innerHeight;
    prog.style.width = (h > 0 ? (scrollY / h) * 100 : 0) + "%";
  };
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const burger = $("#burger"), links = $("#navLinks");
  burger?.addEventListener("click", () => links.classList.toggle("open"));
  $$("#navLinks a").forEach(a => a.addEventListener("click", () => links.classList.remove("open")));

  /* ---------- reveal ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { threshold: .12 });
  $$(".reveal").forEach(el => io.observe(el));

  /* ---------- count up ---------- */
  const cIO = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target, end = +el.dataset.count, suf = el.dataset.suffix || "";
    if (reduce) { el.textContent = end + suf; cIO.unobserve(el); return; }
    let t0 = null;
    const step = ts => {
      if (t0 === null) t0 = ts;
      const p = Math.min((ts - t0) / 1400, 1);
      el.textContent = Math.floor((1 - Math.pow(1 - p, 3)) * end) + suf;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
    cIO.unobserve(el);
  }), { threshold: .6 });
  $$("[data-count]").forEach(el => cIO.observe(el));

  /* ---------- magnetic + tilt ---------- */
  if (!reduce && canHover) {
    $$("[data-magnetic]").forEach(el => {
      el.addEventListener("mousemove", e => {
        const r = el.getBoundingClientRect();
        el.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * .3}px,${(e.clientY - r.top - r.height / 2) * .4}px)`;
      });
      el.addEventListener("mouseleave", () => el.style.transform = "");
    });
    $$("[data-tilt]").forEach(el => {
      el.addEventListener("mousemove", e => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - .5, py = (e.clientY - r.top) / r.height - .5;
        el.style.transform = `perspective(700px) rotateY(${px * 8}deg) rotateX(${-py * 8}deg) translateY(-4px)`;
      });
      el.addEventListener("mouseleave", () => el.style.transform = "");
    });
  }

  /* ---------- hero blob ---------- */
  const blob = $("[data-blob]");
  if (blob && !reduce && canHover) {
    let bx = innerWidth * .6, by = innerHeight * .45, tx = bx, ty = by;
    addEventListener("mousemove", e => { tx = e.clientX; ty = e.clientY; });
    (function bl() { bx += (tx - bx) * .05; by += (ty - by) * .05; blob.style.left = bx + "px"; blob.style.top = by + "px"; requestAnimationFrame(bl); })();
  }

  /* ---------- marquee ---------- */
  const track = $("[data-marquee]");
  if (track && !reduce) {
    let x = 0; const w = track.scrollWidth / 2;
    (function m() { x = (x - .5) % w; track.style.transform = `translateX(${x}px)`; requestAnimationFrame(m); })();
  }

  const esc = s => s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = n => n >= 1000 ? (n / 1000).toFixed(1) + "k" : n;

  /* native top-languages bar (reliable — no external image service) */
  const LANG_COLORS = { JavaScript:"#f1e05a", TypeScript:"#3178c6", HTML:"#e34c26", CSS:"#563d7c",
    SCSS:"#c6538c", Python:"#3572A5", Java:"#b07219", "C++":"#f34b7d", C:"#555555", "C#":"#178600",
    PHP:"#4F5D95", Ruby:"#701516", Go:"#00ADD8", Rust:"#dea584", Shell:"#89e051", Dart:"#00B4AB",
    Kotlin:"#A97BFF", Swift:"#F05138", Vue:"#41b883", Astro:"#ff5a03", Jupyter:"#DA5B0B" };
  function renderLangs(repos) {
    const el = document.getElementById("ghLangs");
    if (!el) return;
    const count = {};
    repos.forEach(r => { if (r.language) count[r.language] = (count[r.language] || 0) + 1; });
    const entries = Object.entries(count).sort((a, b) => b[1] - a[1]);
    if (!entries.length) { el.style.display = "none"; return; }
    const total = entries.reduce((s, [, n]) => s + n, 0);
    const top = entries.slice(0, 8);
    const pct = n => (n / total * 100).toFixed(1);
    el.innerHTML = `
      <h3 class="gh-langs__title">Most used languages</h3>
      <div class="gh-langs__bar">${top.map(([l, n]) => `<span style="width:${pct(n)}%;background:${LANG_COLORS[l] || "#ff5a3c"}" title="${esc(l)} ${pct(n)}%"></span>`).join("")}</div>
      <div class="gh-langs__legend">${top.map(([l, n]) => `<span><i style="background:${LANG_COLORS[l] || "#ff5a3c"}"></i>${esc(l)} <b>${pct(n)}%</b></span>`).join("")}</div>`;
  }

  /* ============================================================
     LIVE GITHUB — profile stats + language bar.
     The project cards themselves are static HTML written by
     tools/build.py, so crawlers see them without running this.
     ============================================================ */
  $$("#projectsGrid .project").forEach(card => card.addEventListener("mousemove", e => {
    const b = card.getBoundingClientRect();
    card.style.setProperty("--mx", (e.clientX - b.left) + "px");
    card.style.setProperty("--my", (e.clientY - b.top) + "px");
  }));

  fetch(`https://api.github.com/users/${GH_USER}`)
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(u => {
      $("#ghRepos").textContent = u.public_repos ?? "—";
      $("#ghFollowers").textContent = u.followers ?? "—";
      $("#ghGists").textContent = u.public_gists ?? "—";
    }).catch(() => {});

  fetch(`https://api.github.com/users/${GH_USER}/repos?per_page=100&sort=updated`)
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(repos => {
      if (!Array.isArray(repos)) throw 0;
      const owned = repos.filter(r => !r.fork);
      $("#ghStars").textContent = fmt(owned.reduce((s, r) => s + r.stargazers_count, 0));
      renderLangs(owned);
    })
    .catch(() => { $("#ghLangs").style.display = "none"; });

  /* ---------- old blog links ----------
     Posts used to open in an overlay at /#post/<slug>. They are static pages
     now, so send any old link to the real URL. */
  const legacy = location.hash.match(/^#post\/([\w-]+)$/);
  if (legacy) location.replace(`/blog/${legacy[1]}/`);

  /* ============================================================
     CONTACT FORM
     Posts over fetch so the visitor stays on the page. If the
     endpoint is down or blocked, the message is handed to the
     visitor's own mail app instead — it is never silently lost.
     With JS off the form still does a normal POST (action attr)
     and lands on thankyou.html.
     ============================================================ */
  const cForm = $("#contactForm");
  if (cForm) {
    const status = $("#formStatus");
    const submit = cForm.querySelector('button[type="submit"]');
    const say = (msg, state) => { status.textContent = msg; status.dataset.state = state || ""; };

    const mailtoFor = d => "mailto:" + CONTACT.email +
      "?subject=" + encodeURIComponent("Portfolio message from " + (d.name || "someone")) +
      "&body=" + encodeURIComponent(`${d.message || ""}

— ${d.name || ""} (${d.email || ""})`);

    /* optional Discord mirror — instant phone push, no inbox needed */
    const mirror = d => {
      if (!CONTACT.discord) return Promise.resolve();
      return fetch(CONTACT.discord, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: `**${d.name}** <${d.email}>
${d.message}`.slice(0, 1900) })
      }).catch(() => {});
    };

    cForm.addEventListener("submit", async e => {
      e.preventDefault();
      const d = Object.fromEntries(new FormData(cForm));
      if (d._honey) return;                       // hidden field: only bots fill it
      submit.disabled = true;
      say("Sending…", "busy");
      try {
        const res = await fetch(CONTACT.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({
            name: d.name, email: d.email, message: d.message,
            _subject: d._subject, _template: "table", _captcha: "false"
          })
        });
        if (!res.ok) throw new Error(res.status);
        mirror(d);
        cForm.reset();
        say(`Sent ✓ — I'll reply to ${d.email} soon.`, "ok");
      } catch {
        mirror(d);
        say("The form service didn't answer — opening your mail app so nothing is lost.", "err");
        location.href = mailtoFor(d);
      } finally {
        submit.disabled = false;
      }
    });

    /* instant channels, only the ones that are configured */
    const alt = $("#altChannels");
    const greeting = encodeURIComponent("Hi Abdul — I saw your portfolio and");
    const links = [
      CONTACT.whatsapp && [`https://wa.me/${CONTACT.whatsapp}?text=${greeting}`, "WhatsApp"],
      CONTACT.telegram && [`https://t.me/${CONTACT.telegram}`, "Telegram"],
      CONTACT.email    && [`mailto:${CONTACT.email}`, "Email"]
    ].filter(Boolean);
    if (links.length) {
      alt.hidden = false;
      for (const [href, label] of links) {
        const a = document.createElement("a");
        a.className = "alt-btn";
        a.href = href;
        a.textContent = label;
        a.setAttribute("data-hover", "");
        if (href.startsWith("http")) { a.target = "_blank"; a.rel = "noopener"; }
        alt.appendChild(a);
      }
    }
  }
})();
