/* ============================================================
   Abdul Manan — portfolio  ·  interactions, theme, GitHub blog
   ------------------------------------------------------------
   EDIT THESE if you rename things:
     GH_USER  = your GitHub username (projects + stats)
     BLOG     = where your blog markdown lives on GitHub
   Add a .md file to that repo/folder and it shows up here.
   ============================================================ */
(() => {
  "use strict";

  const GH_USER = "abdulmanan69";
  const BLOG = {
    user:   "abdulmanan69",   // repo owner
    repo:   "portfolio",      // posts live in the same repo as the site
    path:   "posts",          // folder inside the repo that holds *.md files
    branch: "main"            // default branch
  };
  const AUTHOR = "Abdul Manan";
  const SITE   = "https://abdulmanan.tech";

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
     LIVE GITHUB — profile stats + auto project cards
     ============================================================ */
  const ICONS = ["◆","▲","●","✦","◈","❖","✳","◐"];
  const grid = $("#projectsGrid");

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
      const top = owned.sort((a, b) =>
        (b.stargazers_count - a.stargazers_count) || (new Date(b.pushed_at) - new Date(a.pushed_at))
      ).slice(0, 6);
      if (!top.length) { grid.innerHTML = `<div class="projects__loading">No public repos yet.</div>`; return; }
      grid.innerHTML = top.map((r, i) => `
        <a class="project reveal" href="${r.homepage || r.html_url}" target="_blank" rel="noopener" data-hover>
          <div class="project__top">
            <span class="project__icon">${ICONS[i % ICONS.length]}</span>
            ${r.language ? `<span class="project__lang"><span class="project__dot"></span>${esc(r.language)}</span>` : ""}
          </div>
          <h3>${esc(r.name.replace(/[-_]/g, " "))}</h3>
          <p>${r.description ? esc(r.description) : "A project I've been building — click to explore the code."}</p>
          <div class="project__meta"><span>★ ${r.stargazers_count}</span><span>⑂ ${r.forks_count}</span><span>${new Date(r.pushed_at).getFullYear()}</span></div>
        </a>`).join("");
      $$("#projectsGrid .reveal").forEach(el => io.observe(el));
      window.__rebindCursor?.();
      $$("#projectsGrid .project").forEach(card => card.addEventListener("mousemove", e => {
        const b = card.getBoundingClientRect();
        card.style.setProperty("--mx", (e.clientX - b.left) + "px");
        card.style.setProperty("--my", (e.clientY - b.top) + "px");
      }));
    })
    .catch(() => {
      grid.innerHTML = `<div class="projects__loading">Couldn't load repos —
        <a class="link-underline" href="https://github.com/${GH_USER}?tab=repositories" target="_blank" rel="noopener">view on GitHub →</a></div>`;
    });

  /* ============================================================
     GITHUB-DRIVEN BLOG
     Reads markdown files from  github.com/USER/REPO/PATH
     Each .md may start with YAML front-matter:
       ---
       title: My post
       date: 2026-07-24
       excerpt: One line for the card + SEO.
       cover: https://link-to-image.png
       tags: web, design
       ---
       Body in **markdown**, images, code, etc.
     ============================================================ */
  const blogGrid = $("#blogGrid");
  const reader = $("#reader"), readerBody = $("#readerBody");
  let POSTS = [];

  const slugify = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  function parseFrontMatter(raw) {
    const m = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);
    if (!m) return { meta: {}, body: raw };
    const meta = {};
    m[1].split("\n").forEach(line => {
      const i = line.indexOf(":");
      if (i > -1) meta[line.slice(0, i).trim().toLowerCase()] = line.slice(i + 1).trim().replace(/^["']|["']$/g, "");
    });
    return { meta, body: m[2] };
  }

  const prettyDate = d => {
    const t = new Date(d);
    return isNaN(t) ? "" : t.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  };

  fetch(`https://api.github.com/repos/${BLOG.user}/${BLOG.repo}/contents/${BLOG.path}?ref=${BLOG.branch}`)
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(files => {
      const mds = (Array.isArray(files) ? files : []).filter(f => f.type === "file" && /\.md$/i.test(f.name) && f.name.toLowerCase() !== "readme.md");
      if (!mds.length) return showEmptyBlog();
      return Promise.all(mds.map(f =>
        fetch(f.download_url).then(r => r.text()).then(raw => {
          const { meta, body } = parseFrontMatter(raw);
          const title = meta.title || f.name.replace(/\.md$/i, "").replace(/[-_]/g, " ");
          return {
            slug: slugify(meta.slug || title),
            title,
            date: meta.date || "",
            excerpt: meta.excerpt || body.replace(/[#>*`_!\[\]()-]/g, "").trim().slice(0, 140),
            cover: meta.cover || "",
            tags: (meta.tags || "").split(",").map(s => s.trim()).filter(Boolean),
            body
          };
        }).catch(() => null)
      ));
    })
    .then(posts => {
      if (!posts) return;
      POSTS = posts.filter(Boolean).sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
      if (!POSTS.length) return showEmptyBlog();
      renderBlogList();
      routeFromHash();
    })
    .catch(() => showEmptyBlog(true));

  function showEmptyBlog(errored) {
    blogGrid.innerHTML = `<div class="blog__empty">
      <p style="margin-bottom:10px"><strong>No posts yet.</strong> ${errored ? "(couldn't reach the blog repo) " : ""}Here's how to publish one:</p>
      <p>1. In the <code>${BLOG.repo}</code> repo, open the <code>${BLOG.path}/</code> folder.<br>
         2. Add a <code>my-post.md</code> file in it.<br>
         3. Start the file with front-matter (title, date, excerpt, cover) — then write in markdown.<br>
         4. Commit. Refresh this page. It appears automatically. ✨</p>
    </div>`;
  }

  function renderBlogList() {
    blogGrid.innerHTML = POSTS.map(p => `
      <article class="post reveal" data-hover data-slug="${p.slug}">
        ${p.cover ? `<img class="post__cover" loading="lazy" alt="${esc(p.title)}" src="${esc(p.cover)}">` : ""}
        <div class="post__body">
          <span class="post__date">${prettyDate(p.date)}</span>
          <h3>${esc(p.title)}</h3>
          <p>${esc(p.excerpt)}</p>
          ${p.tags.length ? `<div class="post__tags">${p.tags.map(t => `<span>#${esc(t)}</span>`).join("")}</div>` : ""}
        </div>
      </article>`).join("");
    $$("#blogGrid .post").forEach(el => {
      io.observe(el);
      el.addEventListener("click", () => location.hash = "post/" + el.dataset.slug);
    });
    window.__rebindCursor?.();
  }

  function openPost(slug) {
    const p = POSTS.find(x => x.slug === slug);
    if (!p) return closeReader();
    readerBody.innerHTML = `
      <h1>${esc(p.title)}</h1>
      <div class="reader__meta">By ${esc(AUTHOR)}${p.date ? " · " + prettyDate(p.date) : ""}${p.tags.length ? " · " + p.tags.map(t => "#" + esc(t)).join(" ") : ""}</div>
      ${p.cover ? `<img alt="${esc(p.title)}" src="${esc(p.cover)}">` : ""}
      <div>${window.marked ? marked.parse(p.body) : esc(p.body)}</div>`;
    reader.classList.add("open");
    reader.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    reader.scrollTop = 0;
    setSEO(p);
    window.__rebindCursor?.();
  }

  function closeReader() {
    reader.classList.remove("open");
    reader.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    resetSEO();
  }

  /* per-post SEO: title, description, canonical + BlogPosting structured data */
  const baseTitle = document.title;
  const baseDesc = $('meta[name="description"]').content;
  function setSEO(p) {
    document.title = `${p.title} — ${AUTHOR}`;
    $('meta[name="description"]').content = p.excerpt;
    let ld = $("#ldPost");
    if (!ld) { ld = document.createElement("script"); ld.type = "application/ld+json"; ld.id = "ldPost"; document.head.appendChild(ld); }
    ld.textContent = JSON.stringify({
      "@context": "https://schema.org", "@type": "BlogPosting",
      headline: p.title, description: p.excerpt,
      author: { "@type": "Person", name: AUTHOR, url: SITE },
      datePublished: p.date || undefined,
      image: p.cover || undefined,
      keywords: p.tags.join(", "),
      mainEntityOfPage: `${SITE}/#post/${p.slug}`
    });
  }
  function resetSEO() {
    document.title = baseTitle;
    $('meta[name="description"]').content = baseDesc;
    $("#ldPost")?.remove();
  }

  function routeFromHash() {
    const m = location.hash.match(/^#post\/(.+)$/);
    if (m) openPost(decodeURIComponent(m[1])); else closeReader();
  }
  addEventListener("hashchange", routeFromHash);
  $("#readerBack").addEventListener("click", () => { location.hash = "blog"; });
  $("#readerClose").addEventListener("click", () => { location.hash = "blog"; });
  addEventListener("keydown", e => { if (e.key === "Escape" && reader.classList.contains("open")) location.hash = "blog"; });
})();
