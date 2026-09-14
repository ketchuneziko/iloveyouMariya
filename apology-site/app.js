/* ============================================================
   ТЫ ИЗМЕНИЛА МОЮ ВСЕЛЕННУЮ — магия
   ============================================================ */

/* ═══════════════════════════════════════════════════════════
   ✏️ НАСТРОЙКИ — поменяй всё под себя прямо здесь
   ═══════════════════════════════════════════════════════════ */
const CONFIG = {
  yourName: "[Твоё имя]",            // как подписываешься ты
  herName: "[Имя]",                  // её имя
  startDate: "2023-05-14",           // дата, с которой считаем «дней вместе» (ГГГГ-ММ-ДД)

  constellationText: "ты + я",       // подпись под созвездием

  milestones: [
    { date: "2023-05-14", title: "День, когда мы встретились",
      text: "Я тогда ещё не знал, что в этот день началась моя настоящая жизнь." },
    { date: "2023-06-01", title: "Наш первый разговор до утра",
      text: "Я понял: с тобой можно говорить обо всём на свете — и не хотеть останавливаться." },
    { date: "2023-07-10", title: "Первая прогулка",
      text: "Город стал другим. Наверное, это ты его перекрасила." },
    { date: "2023-09-22", title: "Момент, когда я понял, что влюбился",
      text: "Я не записал точную минуту. Но я запомнил её навсегда." },
    { date: "2024-01-01", title: "Первый Новый год вместе",
      text: "Лучший салют был не в небе, а рядом со мной." },
    { date: "today", title: "Сегодня",
      text: "Я пишу этот сайт, потому что ты заслуживаешь целую вселенную. И я готов строить её для тебя." },
  ],

  reasons: [
    { emoji: "☀️", text: "За то, как ты смеёшься — от этого у меня внутри что-то переворачивается" },
    { emoji: "🌙", text: "За твои «спокойной ночи» — после них мне правда снится лучшее" },
    { emoji: "🔥", text: "За то, что рядом с тобой я становлюсь лучше, чем был вчера" },
    { emoji: "🎧", text: "За то, что с тобой даже молчать уютно" },
    { emoji: "🗺️", text: "За то, что с тобой любой план — уже приключение" },
    { emoji: "🍜", text: "За то, как ты заботишься обо мне, даже когда я этого не замечаю" },
    { emoji: "✨", text: "За твой взгляд, в котором я вижу наше будущее" },
    { emoji: "🫂", text: "За твои объятия — это моё самое безопасное место на Земле" },
    { emoji: "💬", text: "За то, что ты умеешь слушать — по-настоящему" },
    { emoji: "🎀", text: "За твою красоту — снаружи, но особенно внутри" },
    { emoji: "🛡️", text: "За то, что ты веришь в меня, даже когда я сам не верю" },
    { emoji: "♾️", text: "За то, что ты — это ты. Просто это и есть главная причина" },
  ],

  counters: [
    { id: "days", value: null, label: "дней вместе" },          // считается сам
    { id: "c", value: 4217, label: "улыбок, подаренных тобой" },
    { id: "c", value: 87, label: "бессонных ночей за разговорами" },
    { id: "c", value: 1000000, label: "моментов, которые хочу повторить" },
  ],
};

/* ── Утилиты ───────────────────────────────────────────── */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];
const rand = (min, max) => Math.random() * (max - min) + min;
const randInt = (min, max) => Math.floor(rand(min, max + 1));
const TAU = Math.PI * 2;
const isTouch = window.matchMedia("(pointer: coarse)").matches;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const DPR = Math.min(window.devicePixelRatio || 1, 2);

/* ═══════════════════════════════════════════════════════════
   КАНВАС: живой космос (звёзды, падающие звёзды, сердца)
   ═══════════════════════════════════════════════════════════ */
const bgCanvas = $("#bg-canvas");
const bgCtx = bgCanvas.getContext("2d");
let W = 0, H = 0, scrollOffset = 0;

function resizeBg() {
  W = bgCanvas.width = innerWidth * DPR;
  H = bgCanvas.height = innerHeight * DPR;
  bgCanvas.style.width = innerWidth + "px";
  bgCanvas.style.height = innerHeight + "px";
}

const starCount = isTouch ? 90 : 190;
const stars = Array.from({ length: starCount }, () => ({
  x: Math.random(), y: Math.random(),
  r: rand(0.4, 1.6) * DPR,
  base: rand(0.25, 0.85),
  tw: rand(0, TAU),
  twSpeed: rand(0.4, 1.6),
  depth: rand(0.25, 1),
  hue: Math.random() < 0.22 ? rand(340, 360) : Math.random() < 0.14 ? rand(40, 55) : 220,
}));

const shooters = [];
function spawnShooter() {
  if (reducedMotion) return;
  const fromTop = Math.random() < 0.6;
  shooters.push({
    x: rand(0.15, 0.85) * W,
    y: fromTop ? rand(-0.1, 0.2) * H : rand(0.15, 0.4) * H,
    vx: rand(2.2, 4.6) * DPR * (Math.random() < 0.5 ? 1 : 1),
    vy: rand(1.6, 3.2) * DPR,
    life: 1,
  });
}
setInterval(spawnShooter, reducedMotion ? 999999 : rand(3500, 8000));
if (!reducedMotion) spawnShooter();

const floatHearts = [];
function spawnFloatingHeart() {
  if (reducedMotion) return;
  floatHearts.push({
    x: rand(0.05, 0.95) * W,
    y: H + 40 * DPR,
    size: rand(8, 20) * DPR,
    vy: rand(0.35, 0.85) * DPR,
    sway: rand(0, TAU),
    swaySpeed: rand(0.5, 1.4),
    alpha: 0,
    fadeIn: rand(1.5, 3),
  });
}
setInterval(spawnFloatingHeart, reducedMotion ? 999999 : 5200);
if (!reducedMotion) { spawnFloatingHeart(); setTimeout(spawnFloatingHeart, 2200); }

function drawHeart(ctx, x, y, size, color, alpha) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(size / 24, size / 24);
  ctx.beginPath();
  ctx.moveTo(0, 7);
  ctx.bezierCurveTo(-12, -6, -7, -14, 0, -7);
  ctx.bezierCurveTo(7, -14, 12, -6, 0, 7);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.globalAlpha = alpha;
  ctx.fill();
  ctx.restore();
}

function drawBg(now) {
  bgCtx.clearRect(0, 0, W, H);

  // звёзды (с лёгким параллаксом)
  for (const s of stars) {
    const twinkle = 0.6 + 0.4 * Math.sin(now * 0.001 * s.twSpeed + s.tw);
    const a = s.base * twinkle;
    const y = ((s.y * H) - scrollOffset * s.depth * 0.12) % H;
    const yy = y < 0 ? y + H : y;
    bgCtx.beginPath();
    bgCtx.arc(s.x * W, yy, s.r, 0, TAU);
    bgCtx.fillStyle = `hsla(${s.hue}, 90%, 82%, ${a})`;
    bgCtx.shadowColor = `hsla(${s.hue}, 90%, 70%, ${a})`;
    bgCtx.shadowBlur = s.r * 4;
    bgCtx.fill();
    bgCtx.shadowBlur = 0;
  }

  // падающие звёзды
  for (let i = shooters.length - 1; i >= 0; i--) {
    const sh = shooters[i];
    sh.x += sh.vx; sh.y += sh.vy; sh.life -= 0.012;
    if (sh.life <= 0 || sh.x > W + 120 * DPR || sh.y > H + 120 * DPR) { shooters.splice(i, 1); continue; }
    const tail = 90 * DPR;
    const grad = bgCtx.createLinearGradient(sh.x, sh.y, sh.x - sh.vx * 22, sh.y - sh.vy * 22);
    grad.addColorStop(0, `rgba(255, 235, 210, ${0.9 * sh.life})`);
    grad.addColorStop(1, "rgba(255, 235, 210, 0)");
    bgCtx.strokeStyle = grad;
    bgCtx.lineWidth = 1.6 * DPR;
    bgCtx.beginPath();
    bgCtx.moveTo(sh.x, sh.y);
    bgCtx.lineTo(sh.x - sh.vx * 22, sh.y - sh.vy * 22);
    bgCtx.stroke();
  }

  // всплывающие сердца
  for (let i = floatHearts.length - 1; i >= 0; i--) {
    const h = floatHearts[i];
    h.y -= h.vy;
    h.sway += 0.02 * h.swaySpeed;
    h.alpha = Math.min(1, h.alpha + 0.004 * h.fadeIn);
    if (h.y < -60 * DPR) { floatHearts.splice(i, 1); continue; }
    const x = h.x + Math.sin(h.sway) * 26 * DPR;
    drawHeart(bgCtx, x, h.y, h.size, `hsla(${340 + Math.sin(h.sway) * 14}, 95%, 72%, ${h.alpha * 0.5})`, h.alpha * 0.55);
  }
}

/* ═══════════════════════════════════════════════════════════
   КАНВАС ЭФФЕКТОВ: сердца-салюты при клике + след курсора
   ═══════════════════════════════════════════════════════════ */
const fxCanvas = $("#fx-canvas");
const fxCtx = fxCanvas.getContext("2d");
fxCanvas.width = innerWidth * DPR;
fxCanvas.height = innerHeight * DPR;

const fx = [];
const sparkles = [];

function heartBurst(x, y, count = 16, power = 1) {
  const colors = ["#ff7ea8", "#ffb3c9", "#ffd27d", "#b38bff", "#ff5f8f"];
  for (let i = 0; i < count; i++) {
    const angle = rand(0, TAU);
    const speed = rand(1.5, 6.5) * power;
    fx.push({
      type: "heart",
      x, y,
      vx: Math.cos(angle) * speed * DPR,
      vy: Math.sin(angle) * speed * DPR - 1.5 * DPR,
      size: rand(7, 16) * DPR * power,
      rot: rand(0, TAU),
      vr: rand(-0.12, 0.12),
      life: 1,
      decay: rand(0.008, 0.02),
      color: colors[randInt(0, colors.length - 1)],
    });
  }
  for (let i = 0; i < count / 2; i++) {
    const angle = rand(0, TAU);
    const speed = rand(2, 9) * power;
    fx.push({
      type: "spark",
      x, y,
      vx: Math.cos(angle) * speed * DPR,
      vy: Math.sin(angle) * speed * DPR,
      size: rand(1.2, 2.6) * DPR,
      life: 1,
      decay: rand(0.02, 0.045),
      color: "#fff",
    });
  }
}

function bigExplosion(x, y, count = 60) {
  heartBurst(x, y, count, 1.7);
  heartBurst(x - 40 * DPR, y + 20 * DPR, count / 2, 1.2);
  heartBurst(x + 40 * DPR, y + 20 * DPR, count / 2, 1.2);
}

function drawFx(now) {
  fxCtx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);

  for (let i = fx.length - 1; i >= 0; i--) {
    const p = fx[i];
    p.x += p.vx; p.y += p.vy;
    p.vy += 0.12 * DPR;
    p.life -= p.decay;
    p.rot += p.vr;
    if (p.life <= 0) { fx.splice(i, 1); continue; }
    if (p.type === "heart") {
      fxCtx.save();
      fxCtx.translate(p.x, p.y);
      fxCtx.rotate(p.rot);
      fxCtx.globalAlpha = Math.max(0, p.life);
      drawHeart(fxCtx, 0, 0, p.size, p.color, 1);
      fxCtx.restore();
    } else {
      fxCtx.beginPath();
      fxCtx.arc(p.x, p.y, p.size * p.life, 0, TAU);
      fxCtx.fillStyle = `rgba(255, 240, 250, ${Math.max(0, p.life)})`;
      fxCtx.shadowColor = "rgba(255, 178, 201, 0.9)";
      fxCtx.shadowBlur = 8 * DPR;
      fxCtx.fill();
      fxCtx.shadowBlur = 0;
    }
  }

  // след курсора
  for (let i = sparkles.length - 1; i >= 0; i--) {
    const s = sparkles[i];
    s.life -= 0.025;
    if (s.life <= 0) { sparkles.splice(i, 1); continue; }
    fxCtx.beginPath();
    fxCtx.arc(s.x, s.y, s.r * s.life, 0, TAU);
    fxCtx.fillStyle = `rgba(255, 190, 214, ${s.life * 0.5})`;
    fxCtx.fill();
  }
}

/* клики — салют */
addEventListener("pointerdown", (e) => {
  if (e.target.closest("button, a, .intro")) return;
  heartBurst(e.clientX * DPR, e.clientY * DPR, isTouch ? 10 : 14);
});

/* след курсора */
if (!isTouch && !reducedMotion) {
  addEventListener("pointermove", (e) => {
    if (Math.random() < 0.5) {
      sparkles.push({ x: e.clientX * DPR, y: e.clientY * DPR, r: rand(0.8, 2.2) * DPR, life: 1 });
    }
  });
}

/* ═══════════════════════════════════════════════════════════
   КАСТОМНЫЙ КУРСОР
   ═══════════════════════════════════════════════════════════ */
if (!isTouch && !reducedMotion) {
  const dot = $("#cursor-dot");
  const ring = $("#cursor-ring");
  let mx = innerWidth / 2, my = innerHeight / 2;
  let rx = mx, ry = my;
  document.body.classList.add("cursor-active");

  addEventListener("pointermove", (e) => {
    mx = e.clientX; my = e.clientY;
    dot.style.left = mx + "px";
    dot.style.top = my + "px";
    const target = e.target.closest("a, button, .reason, .tl-card, .stat");
    document.body.classList.toggle("cursor-hover", !!target);
  });
  (function cursorLoop() {
    rx += (mx - rx) * 0.16;
    ry += (my - ry) * 0.16;
    ring.style.left = rx + "px";
    ring.style.top = ry + "px";
    requestAnimationFrame(cursorLoop);
  })();
}

/* ═══════════════════════════════════════════════════════════
   ГЕНЕРАТИВНАЯ МУЗЫКА (Web Audio, без файлов)
   ═══════════════════════════════════════════════════════════ */
const AudioEngine = {
  ctx: null,
  master: null,
  playing: false,
  chordTimer: null,
  pluckTimer: null,
  chords: [
    [174.61, 220.00, 261.63, 329.63], // Fmaj7
    [164.81, 220.00, 261.63, 329.63], // Dm7
    [130.81, 196.00, 246.94, 293.66], // Cmaj7
    [146.83, 220.00, 293.66, 349.23], // Dm7/G
  ],
  pentatonic: [349.23, 392.00, 440.00, 523.25, 587.33], // F pentatonic

  start() {
    if (this.playing) return;
    this.ctx = this.ctx || new (window.AudioContext || window.webkitAudioContext)();
    if (this.ctx.state === "suspended") this.ctx.resume();
    this.master = this.master || (() => {
      const g = this.ctx.createGain();
      g.gain.value = 0;
      g.connect(this.ctx.destination);
      return g;
    })();
    this.master.gain.linearRampToValueAtTime(0.5, this.ctx.currentTime + 3);
    this.playing = true;
    this.playChord(0);
    this.schedulePluck();
    $("#music-toggle").classList.add("playing");
  },

  stop() {
    this.playing = false;
    clearTimeout(this.chordTimer);
    clearTimeout(this.pluckTimer);
    if (this.master && this.ctx) {
      this.master.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 1.2);
    }
    $("#music-toggle").classList.remove("playing");
  },

  playChord(idx) {
    if (!this.playing || !this.ctx) return;
    const t = this.ctx.currentTime;
    const chord = this.chords[idx % this.chords.length];
    const filter = this.ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 900;
    filter.connect(this.master);
    chord.forEach((f, i) => {
      const osc = this.ctx.createOscillator();
      osc.type = i < 2 ? "sine" : "triangle";
      osc.frequency.value = f;
      const g = this.ctx.createGain();
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.055, t + 3.2);
      g.gain.setValueAtTime(0.055, t + 6);
      g.gain.linearRampToValueAtTime(0, t + 11);
      osc.connect(g); g.connect(filter);
      osc.start(t); osc.stop(t + 11.5);
    });
    this.chordTimer = setTimeout(() => this.playChord(idx + 1), 8000);
  },

  schedulePluck() {
    if (!this.playing || !this.ctx) return;
    const t = this.ctx.currentTime;
    const f = this.pentatonic[randInt(0, this.pentatonic.length - 1)];
    const osc = this.ctx.createOscillator();
    osc.type = "sine";
    osc.frequency.value = f;
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(0.035, t + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 2.8);
    const pan = this.ctx.createStereoPanner();
    pan.pan.value = rand(-0.6, 0.6);
    osc.connect(g); g.connect(pan); pan.connect(this.master);
    osc.start(t); osc.stop(t + 3);
    this.pluckTimer = setTimeout(() => this.schedulePluck(), rand(1400, 2800));
  },
};

const musicToggle = $("#music-toggle");
musicToggle.addEventListener("click", () => {
  AudioEngine.playing ? AudioEngine.stop() : AudioEngine.start();
});

/* ═══════════════════════════════════════════════════════════
   ИНТРО
   ═══════════════════════════════════════════════════════════ */
const intro = $("#intro");
setTimeout(() => intro.classList.add("show"), 300);

$("#intro-btn").addEventListener("click", () => {
  intro.classList.add("gone");
  $("#main").classList.remove("hidden");
  AudioEngine.start();
  heartBurst(innerWidth / 2 * DPR, innerHeight / 2 * DPR, 26, 1.4);
  setTimeout(() => { intro.remove(); buildConstellation(); }, 1400);
});

/* ═══════════════════════════════════════════════════════════
   ПОЯВЛЕНИЕ ПРИ ПРОКРУТКЕ, ПРОГРЕСС, НАВИГАЦИЯ
   ═══════════════════════════════════════════════════════════ */
const nav = $("#nav");
const io = new IntersectionObserver((entries) => {
  entries.forEach((en) => {
    if (en.isIntersecting) { en.target.classList.add("visible"); io.unobserve(en.target); }
  });
}, { threshold: 0.15 });
$$(".reveal").forEach((el) => io.observe(el));

const progressBar = $("#scroll-progress-bar");
addEventListener("scroll", () => {
  const max = document.documentElement.scrollHeight - innerHeight;
  progressBar.style.width = (max > 0 ? (scrollY / max) * 100 : 0) + "%";
  if (!intro.parentNode) nav.classList.toggle("visible", scrollY > innerHeight * 0.6);
}, { passive: true });

/* ═══════════════════════════════════════════════════════════
   СЧЁТЧИКИ
   ═══════════════════════════════════════════════════════════ */
function daysTogether() {
  const start = new Date(CONFIG.startDate + "T00:00:00");
  const now = new Date();
  if (isNaN(start)) return 0;
  return Math.max(0, Math.floor((now - start) / 86400000));
}

const statsIO = new IntersectionObserver((entries) => {
  entries.forEach((en) => {
    if (!en.isIntersecting) return;
    const el = en.target;
    statsIO.unobserve(el);
    const numEl = el.querySelector(".stat-num");
    const id = el.dataset.count;
    const isDays = id === "days";
    const target = isDays ? daysTogether() : parseInt(id, 10);
    if (target === 0 && !isDays) return;
    const dur = 2200;
    const t0 = performance.now();
    (function tick(t) {
      const p = Math.min(1, (t - t0) / dur);
      const eased = 1 - Math.pow(1 - p, 4);
      const val = Math.round(target * eased);
      numEl.textContent = val.toLocaleString("ru-RU");
      if (p < 1) requestAnimationFrame(tick);
      else numEl.textContent = target.toLocaleString("ru-RU");
    })(t0);
  });
}, { threshold: 0.5 });
$$(".stat").forEach((el) => statsIO.observe(el));

/* ═══════════════════════════════════════════════════════════
   ТАЙМЛАЙН И ПРИЧИНЫ (из CONFIG)
   ═══════════════════════════════════════════════════════════ */
const fmtDate = (d) =>
  d === "today"
    ? "сегодня"
    : new Date(d + "T00:00:00").toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });

const timeline = $("#timeline");
CONFIG.milestones.forEach((m, i) => {
  const item = document.createElement("div");
  item.className = "tl-item reveal";
  item.innerHTML = `
    <span class="tl-dot"></span>
    <div class="tl-card">
      <p class="tl-date">${fmtDate(m.date)}</p>
      <h3 class="tl-title">${m.title}</h3>
      <p class="tl-text">${m.text}</p>
    </div>`;
  timeline.appendChild(item);
  io.observe(item);
});

const reasonsGrid = $("#reasons-grid");
CONFIG.reasons.forEach((r, i) => {
  const card = document.createElement("div");
  card.className = "reason reveal";
  card.style.transitionDelay = (i % 4) * 0.07 + "s";
  card.innerHTML = `<span class="reason-emoji">${r.emoji}</span><p class="reason-text">${r.text}</p>`;
  reasonsGrid.appendChild(card);
  io.observe(card);
});

/* ═══════════════════════════════════════════════════════════
   СОЗВЕЗДИЕ-СЕРДЦЕ
   ═══════════════════════════════════════════════════════════ */
const cosmoCanvas = $("#cosmos-canvas");
const cosmoCtx = cosmoCanvas.getContext("2d");
$("#cosmos-caption").textContent = CONFIG.constellationText;

function heartPoints(n = 72) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const t = (i / n) * TAU;
    const x = 16 * Math.pow(Math.sin(t), 3);
    const y = 13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
    pts.push({ x, y });
  }
  return pts;
}

const cosmoStars = [];
function buildConstellation() {
  const rect = cosmoCanvas.getBoundingClientRect();
  if (rect.width < 10 || rect.height < 10) return; // секция ещё скрыта
  cosmoCanvas.width = rect.width * DPR;
  cosmoCanvas.height = rect.height * DPR;
  const cx = cosmoCanvas.width / 2;
  const cy = cosmoCanvas.height / 2 - 14 * DPR;
  const scale = Math.min(cosmoCanvas.width, cosmoCanvas.height) * 0.028;
  const jitter = scale * 0.22;

  cosmoStars.length = 0;
  const outer = heartPoints(78).map((p) => ({
    x: cx + p.x * scale + rand(-jitter, jitter),
    y: cy - p.y * scale + rand(-jitter, jitter),
    r: rand(0.8, 2.1) * DPR,
    tw: rand(0, TAU),
  }));
  const inner = heartPoints(46).map((p) => ({
    x: cx + p.x * scale * 0.55 + rand(-jitter * 0.6, jitter * 0.6),
    y: cy - p.y * scale * 0.55 + rand(-jitter * 0.6, jitter * 0.6),
    r: rand(0.6, 1.4) * DPR,
    tw: rand(0, TAU),
  }));
  // фоновая пыль внутри сердца
  const dust = Array.from({ length: 90 }, () => ({
    x: cx + rand(-15, 15) * scale,
    y: cy + rand(-13, 8) * scale,
    r: rand(0.3, 0.9) * DPR,
    tw: rand(0, TAU),
  }));
  cosmoStars.push({ group: "outer", pts: outer }, { group: "inner", pts: inner }, { group: "dust", pts: dust });
}
buildConstellation();
new ResizeObserver(buildConstellation).observe(cosmoCanvas);

let cosmoMouse = null;
cosmoCanvas.addEventListener("pointermove", (e) => {
  const rect = cosmoCanvas.getBoundingClientRect();
  cosmoMouse = { x: (e.clientX - rect.left) * DPR, y: (e.clientY - rect.top) * DPR };
});
cosmoCanvas.addEventListener("pointerleave", () => (cosmoMouse = null));

function drawConstellation(now) {
  if (!cosmoStars.length) return; // ещё не построено
  cosmoCtx.clearRect(0, 0, cosmoCanvas.width, cosmoCanvas.height);
  const [outer, inner, dust] = cosmoStars;
  const connect = (pts, color, width) => {
    cosmoCtx.strokeStyle = color;
    cosmoCtx.lineWidth = width;
    cosmoCtx.beginPath();
    pts.forEach((p, i) => { i === 0 ? cosmoCtx.moveTo(p.x, p.y) : cosmoCtx.lineTo(p.x, p.y); });
    cosmoCtx.closePath();
    cosmoCtx.stroke();
  };
  connect(outer.pts, "rgba(179, 139, 255, 0.30)", 1 * DPR);
  connect(inner.pts, "rgba(255, 178, 201, 0.35)", 0.8 * DPR);

  // линии к курсору
  if (cosmoMouse) {
    cosmoCtx.strokeStyle = "rgba(255, 210, 125, 0.25)";
    cosmoCtx.lineWidth = 0.6 * DPR;
    outer.pts.forEach((p) => {
      const d = Math.hypot(p.x - cosmoMouse.x, p.y - cosmoMouse.y);
      if (d < 140 * DPR) {
        cosmoCtx.globalAlpha = 1 - d / (140 * DPR);
        cosmoCtx.beginPath();
        cosmoCtx.moveTo(p.x, p.y);
        cosmoCtx.lineTo(cosmoMouse.x, cosmoMouse.y);
        cosmoCtx.stroke();
      }
    });
    cosmoCtx.globalAlpha = 1;
  }

  for (const { pts } of cosmoStars) {
    for (const p of pts) {
      const a = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(now * 0.0012 + p.tw));
      cosmoCtx.beginPath();
      cosmoCtx.arc(p.x, p.y, p.r, 0, TAU);
      cosmoCtx.fillStyle = `rgba(255, 235, 245, ${a})`;
      cosmoCtx.shadowColor = "rgba(255, 178, 201, 0.9)";
      cosmoCtx.shadowBlur = p.r * 4;
      cosmoCtx.fill();
      cosmoCtx.shadowBlur = 0;
    }
  }

  // пульс сердца
  const pulse = 1 + 0.035 * Math.sin(now * 0.002);
  cosmoCtx.save();
  cosmoCtx.translate(cosmoCanvas.width / 2, cosmoCanvas.height / 2 - 14 * DPR);
  cosmoCtx.scale(pulse, pulse);
  cosmoCtx.globalAlpha = 0.10;
  connect(outer.pts, "rgba(255, 126, 168, 1)", 2 * DPR);
  cosmoCtx.restore();
}

/* ═══════════════════════════════════════════════════════════
   ФИНАЛ: «Простишь меня?»
   ═══════════════════════════════════════════════════════════ */
const btnYes = $("#btn-yes");
const btnNo = $("#btn-no");
const forgiven = $("#forgiven");
let noAttempts = 0;
const noMessages = [
  "Точно? 😢",
  "Подумай ещё раз…",
  "Кнопка сломалась — она тоже считает, что надо простить",
];

function fleeNo() {
  if (noAttempts >= 3) {
    btnNo.textContent = "Ладно, да ❤";
    btnNo.classList.add("no-flee");
    btnNo.removeEventListener("mouseenter", fleeNo);
    btnNo.removeEventListener("click", fleeNo);
    btnNo.addEventListener("click", celebrate);
    return;
  }
  noAttempts++;
  const wrap = btnNo.parentElement;
  const w = wrap.clientWidth - btnNo.offsetWidth - 8;
  const h = wrap.clientHeight - btnNo.offsetHeight - 8;
  btnNo.style.position = "absolute";
  btnNo.style.left = rand(0, Math.max(0, w)) + "px";
  btnNo.style.top = rand(0, Math.max(0, h)) + "px";
  btnNo.textContent = noMessages[Math.min(noAttempts - 1, noMessages.length - 1)];
  heartBurst(
    btnNo.getBoundingClientRect().left * DPR + btnNo.offsetWidth * DPR / 2,
    btnNo.getBoundingClientRect().top * DPR + btnNo.offsetHeight * DPR / 2,
    6, 0.8
  );
}

function celebrate() {
  forgiven.classList.add("show");
  heartBurst(innerWidth / 2 * DPR, innerHeight / 2 * DPR, 40, 1.6);
  bigExplosion(innerWidth * 0.3 * DPR, innerHeight * 0.4 * DPR, 30);
  bigExplosion(innerWidth * 0.7 * DPR, innerHeight * 0.55 * DPR, 30);
  setTimeout(() => bigExplosion(innerWidth / 2 * DPR, innerHeight * 0.7 * DPR, 30), 350);
  if (AudioEngine.playing) setTimeout(() => AudioEngine.playChord(0), 100);
}

btnYes.addEventListener("click", celebrate);
btnNo.addEventListener("mouseenter", fleeNo);
btnNo.addEventListener("click", fleeNo);

$("#btn-hug").addEventListener("click", (e) => {
  const r = e.currentTarget.getBoundingClientRect();
  bigExplosion(r.left * DPR + r.width * DPR / 2, r.top * DPR + r.height * DPR / 2, 40);
});

/* ═══════════════════════════════════════════════════════════
   ПАСХАЛКА: набрать «люблю» или «прости»
   ═══════════════════════════════════════════════════════════ */
let typed = "";
addEventListener("keydown", (e) => {
  if (e.key.length !== 1) return;
  typed = (typed + e.key.toLowerCase()).slice(-6);
  if (typed.endsWith("люблю") || typed.endsWith("прости")) {
    bigExplosion(rand(0.2, 0.8) * innerWidth * DPR, rand(0.2, 0.7) * innerHeight * DPR, 40);
    typed = "";
  }
});

/* ═══════════════════════════════════════════════════════════
   ГЛАВНЫЙ ЦИКЛ
   ═══════════════════════════════════════════════════════════ */
resizeBg();
addEventListener("resize", () => {
  resizeBg();
  fxCanvas.width = innerWidth * DPR;
  fxCanvas.height = innerHeight * DPR;
});

function loop(now) {
  scrollOffset = scrollY;
  drawBg(now);
  drawFx(now);
  drawConstellation(now);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
