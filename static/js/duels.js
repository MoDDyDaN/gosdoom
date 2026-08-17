(() => {
  "use strict";

  const state = {
    duels: [],
    regions: [],
    region: "",
    query: "",
    deputies: [],
    partyInfo: new Map(),
  };

  const $ = (sel) => document.querySelector(sel);

  const chipsBox = $("#duel-region-chips");
  const listBox = $("#duel-list");
  const emptyBox = $("#duel-empty");
  const searchInput = $("#duel-search-input");
  const resultCount = $("#duel-result-count");

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const LOGOS = {
    "Единая Россия": "er",
    "КПРФ": "kprf",
    "ЛДПР": "ldpr",
    "Справедливая Россия": "sr",
    "Новые люди": "nl",
    "Яблоко": "yabloko",
  };

  function logoFile(d) {
    const key = LOGOS[d.party];
    return key ? `/static/images/logos/${key}.svg` : "";
  }

  function initials(d) {
    const parts = d.name.trim().split(/\s+/).filter(Boolean);
    const f = parts[0] ? parts[0][0] : "";
    const g = parts[1] ? parts[1][0] : "";
    return (f + g).toUpperCase();
  }

  function fallbackHtml(d, size) {
    const logo = logoFile(d);
    const cls = size === "lg" ? "card__logo card__logo--lg" : "card__logo";
    return logo
      ? `<img class="${cls}" src="${esc(logo)}" alt="${esc(d.party)}" onerror="this.remove()">`
      : esc(initials(d));
  }

  function cardMediaHtml(d) {
    if (!d.photo) return `<div class="card__fallback">${fallbackHtml(d)}</div>`;
    const logo = logoFile(d) || "";
    return `<img class="card__img" src="${esc(d.photo)}" alt="${esc(d.name)}" loading="lazy" data-logo="${esc(logo)}" onerror="window.__cardFallback(this)">`;
  }

  window.__cardFallback = function (img) {
    const logo = img.getAttribute("data-logo") || "";
    const fb = document.createElement("div");
    fb.className = "card__fallback";
    if (logo) {
      const l = document.createElement("img");
      l.className = "card__logo";
      l.src = logo;
      l.alt = "";
      l.onerror = () => l.remove();
      fb.appendChild(l);
    }
    img.replaceWith(fb);
  };

  function stanceHtml(d) {
    const info = state.partyInfo.get(d.party);
    const own = d.opinions && d.opinions.blocking;
    const b = own && own.short ? own.short : (info ? info.positions.blocking.short : "");
    const title = own && own.full
      ? own.full
      : (info ? `Отношение к блокировкам интернета (позиция партии): ${info.positions.blocking.full}` : "");
    const cls = own && own.short
      ? "card__stance card__stance--blocking card__stance--own"
      : "card__stance card__stance--blocking";
    if (!b) return "";
    return `
      <div class="card__stances">
        <span class="${cls}" title="${esc(title)}">
          <b>Блокировки</b> ${esc(b)}
        </span>
      </div>`;
  }

  function cardHtml(d) {
    return `
      <article class="card" data-id="${esc(d.id)}" tabindex="0" role="button" aria-label="${esc(d.name)}">
        <div class="card__media">
          ${cardMediaHtml(d)}
        </div>
        <div class="party-bar" style="background:${d.color}">
          ${esc(d.party)}
        </div>
        <div class="card__body">
          <h3 class="card__name">${esc(d.name)}</h3>
          ${stanceHtml(d)}
        </div>
        <div class="card__footer">
          <span class="card__badge">Выборы 2026</span>
          <span class="card__more">Подробнее →</span>
        </div>
      </article>`;
  }

  function openModal(d) {
    const rows = [
      ["Партия", d.faction],
      ["Список", d.group],
      ["Округ", d.region],
      ["Номер в списке", d.list_number],
      ["Выборы", d.lead],
    ].filter(([, v]) => v);
    const body = rows.map(([k, v]) => `<div class="modal__row"><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("");
    const info = state.partyInfo.get(d.party);
    const own = d.opinions || {};
    const stances = `
      <div class="modal__stances">
        ${
          info
            ? `<div class="modal__row"><dt>К блокировкам (партия)</dt><dd>${esc(info.positions.blocking.full)}</dd></div>`
            : ""
        }
        ${
          own.blocking && own.blocking.full
            ? `<div class="modal__row"><dt>К блокировкам (личное)</dt><dd>${esc(own.blocking.full)}</dd></div>`
            : ""
        }
        ${
          own.svo && own.svo.full
            ? `<div class="modal__row"><dt>К СВО (личное)</dt><dd>${esc(own.svo.full)}</dd></div>`
            : ""
        }
      </div>`;
    const bills = info && info.bills && info.bills.length && d.was_duty
      ? `
      <div class="modal__bills">
        <h3 class="modal__section-title">Голосование по законопроектам</h3>
        <div class="modal__bill-list">
          ${info.bills
            .map(
              (b) => `
          <div class="modal__bill modal__bill--${esc(b.vote)}">
            <span class="modal__vote modal__vote--${esc(b.vote)}">${esc(b.vote)}</span>
            <div class="modal__bill-info">
              <div class="modal__bill-name">${esc(b.name)}</div>
              <div class="modal__bill-meta">${esc(b.year)} · ${esc(b.note)}</div>
            </div>
          </div>`
            )
            .join("")}
        </div>
        <div class="modal__note">Позиция фракции партии по итогам голосований в Госдуме VIII созыва.</div>
      </div>`
      : "";
    const ownBills = !d.was_duty && own.bills && own.bills.length
      ? `
      <div class="modal__bills">
        <h3 class="modal__section-title">Отношение к законопроектам (личные высказывания)</h3>
        <div class="modal__bill-list">
          ${own.bills
            .map(
              (b) => `
          <div class="modal__bill modal__bill--${esc(b.vote)}">
            <span class="modal__vote modal__vote--${esc(b.vote)}">${esc(b.vote)}</span>
            <div class="modal__bill-info">
              <div class="modal__bill-name">${esc(b.name)}</div>
              <div class="modal__bill-meta">${esc(b.year)} · ${esc(b.note || "")}${b.source ? ` · <a href="${esc(b.source.url)}" target="_blank" rel="noopener">${esc(b.source.label)}</a>` : ""}</div>
            </div>
          </div>`
            )
            .join("")}
        </div>
        <div class="modal__note">Личные высказывания кандидата в интервью и постах (не голосования).</div>
      </div>`
      : "";
    const assets = d.assets && d.assets.length
      ? `
      <div class="modal__assets">
        <h3 class="modal__section-title">Имущественное состояние</h3>
        <div class="modal__assets-list">
          ${d.assets
            .map(
              (a) => `
          <div class="modal__row"><dt>${esc(a.type)}</dt><dd>${esc(a.value)}</dd></div>`
            )
            .join("")}
        </div>
      </div>`
      : "";
    const channels = d.channels && d.channels.length
      ? `
      <div class="modal__channels">
        <h3 class="modal__section-title">Каналы депутата</h3>
        <div class="modal__channels-list">
          ${d.channels
            .map(
              (c) => `
          <a class="modal__channel" href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.label)} ↗</a>`
            )
            .join("")}
        </div>
      </div>`
      : "";
    const source = d.source
      ? `
      <div class="modal__note">Источник: <a href="${esc(d.source.url)}" target="_blank" rel="noopener">${esc(d.source.label)}</a></div>`
      : "";
    const note = d.list_complete
      ? ""
      : `<div class="modal__note">Опубликована только общефедеральная часть списка партии (полный список доступен на сайте ЦИК).</div>`;
    $("#modal").innerHTML = `
      <div class="modal__top">
        ${d.photo
          ? `<img class="modal__img" src="${esc(d.photo)}" alt="${esc(d.name)}">`
          : `<div style="width:100%;aspect-ratio:1.4/1;display:flex;align-items:center;justify-content:center;background:#fff"><img class="card__logo card__logo--lg" src="${esc(logoFile(d))}" alt="${esc(d.party)}" onerror="this.remove()"></div>`}
        <button class="modal__close" aria-label="Закрыть">✕</button>
      </div>
      <div class="modal__body">
        <span class="modal__party" style="background:${d.color}">${esc(d.party)}</span>
        <h2 class="modal__name">${esc(d.name)}</h2>
        <dl class="modal__list">${body}</dl>
        ${stances}
        ${bills}
        ${ownBills}
        ${assets}
        ${channels}
        ${source}
        ${note}
      </div>`;
    $("#modal-backdrop").classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    $("#modal-backdrop").classList.add("hidden");
    document.body.style.overflow = "";
  }

  function render() {
    const q = state.query.toLowerCase();
    const shown = state.duels.filter((d) => {
      if (state.region && d.region !== state.region) return false;
      if (q && !d.a.name.toLowerCase().includes(q) && !d.b.name.toLowerCase().includes(q)) return false;
      return true;
    });

    const html = shown
      .map(
        (d) => `
      <div class="duel-row">
        <span class="duel-region">${esc(d.region)}</span>
        <div class="duel">
          ${cardHtml(d.a)}
          <div class="duel__vs"><span>VS</span></div>
          ${cardHtml(d.b)}
        </div>
      </div>`
      )
      .join("");

    listBox.innerHTML = html;
    emptyBox.classList.toggle("hidden", shown.length > 0);
    if (resultCount) resultCount.innerHTML = `Дуэлей: <b>${shown.length}</b> из ${state.duels.length}`;

    renderChips();
  }

  function renderChips() {
    const all = [
      `<button class="chip ${state.region === "" ? "active" : ""}" data-region="">
         Все регионы <span class="chip__count">${state.duels.length}</span>
       </button>`,
    ];
    for (const r of state.regions) {
      const n = state.duels.filter((d) => d.region === r).length;
      all.push(`
        <button class="chip ${state.region === r ? "active" : ""}" data-region="${esc(r)}">
          ${esc(r)} <span class="chip__count">${n}</span>
        </button>`);
    }
    chipsBox.innerHTML = all.join("");
  }

  chipsBox.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    state.region = chip.dataset.region;
    render();
  });

  searchInput.addEventListener("input", (e) => {
    state.query = e.target.value.trim();
    render();
  });

  listBox.addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (!card) return;
    const d = state.deputies.find((x) => x.id === card.dataset.id);
    if (d) openModal(d);
  });

  listBox.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const card = e.target.closest(".card");
    if (!card) return;
    e.preventDefault();
    const d = state.deputies.find((x) => x.id === card.dataset.id);
    if (d) openModal(d);
  });

  $("#modal-backdrop").addEventListener("click", (e) => {
    if (e.target === $("#modal-backdrop") || e.target.closest(".modal__close")) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  async function init() {
    try {
      const [duels, deputies] = await Promise.all([
        fetch("/api/duels").then((r) => r.json()),
        fetch("/api/deputies?limit=2000").then((r) => r.json()),
      ]);
      const byId = new Map(deputies.items.map((x) => [x.id, x]));
      state.duels = duels.duels.map((d) => ({
        ...d,
        a: { ...(byId.get(d.a.id) || d.a), ...d.a },
        b: { ...(byId.get(d.b.id) || d.b), ...d.b },
      }));
      state.deputies = deputies.items;
      state.regions = duels.regions;
      render();
    } catch (err) {
      listBox.innerHTML = `<div class="empty">Не удалось загрузить данные.</div>`;
      console.error(err);
    }
    try {
      const info = await fetch("/api/parties/info").then((r) => r.json());
      for (const p of info.parties) state.partyInfo.set(p.party, p);
      render();
    } catch (err) {
      console.error(err);
    }
  }

  init();
})();
