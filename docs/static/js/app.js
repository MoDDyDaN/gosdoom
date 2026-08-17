(() => {
  "use strict";

  const state = {
    deputies: [],
    parties: [],
    query: "",
    party: "",
    sort: "az",
  };

  const $ = (sel) => document.querySelector(sel);

  const grid = $("#cards");
  const chips = $("#party-chips");
  const emptyBox = $("#empty");
  const resultCount = $("#result-count");
  const totalStat = $("#total-stat");

  const partyInfo = new Map();

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
    return key ? `static/images/logos/${key}.svg` : "";
  }

  function fallbackHtml(d, size) {
    const logo = logoFile(d);
    const cls = size === "lg" ? "card__logo card__logo--lg" : "card__logo";
    return logo
      ? `<img class="${cls}" src="${esc(logo)}" alt="${esc(d.party)}" onerror="this.remove()">`
      : esc(initials(d));
  }

  function initials(d) {
    const parts = d.name.trim().split(/\s+/).filter(Boolean);
    const f = parts[0] ? parts[0][0] : "";
    const g = parts[1] ? parts[1][0] : "";
    return (f + g).toUpperCase();
  }

  function stanceHtml(d) {
    const info = partyInfo.get(d.party);
    const own = d.opinions && d.opinions.blocking;
    const b = own && own.short ? own.short : (info ? info.positions.blocking.short : "");
    const title = own && own.full
      ? own.full
      : (info ? `Отношение к блокировкам интернета (позиция партии): ${info.positions.blocking.full}` : "");
    const cls = own && own.short ? "card__stance card__stance--blocking card__stance--own" : "card__stance card__stance--blocking";
    return `
      <div class="card__stances">
        <span class="${cls}" title="${esc(title)}">
          <b>Блокировки</b> ${esc(b)}
        </span>
      </div>`;
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

  function cardHtml(d) {
    return `
      <article class="card" data-id="${d.id}" tabindex="0" role="button" aria-label="${esc(d.name)}">
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

  function render() {
    let list = state.deputies.slice();

    if (state.party) list = list.filter((d) => d.party === state.party);
    if (state.query) {
      const q = state.query.toLowerCase();
      list = list.filter((d) => d.name.toLowerCase().includes(q));
    }

    switch (state.sort) {
      case "az": list.sort((a, b) => a.name.localeCompare(b.name, "ru")); break;
      case "za": list.sort((a, b) => b.name.localeCompare(a.name, "ru")); break;
      case "party":
        list.sort((a, b) =>
          a.party.localeCompare(b.party, "ru") || a.name.localeCompare(b.name, "ru")
        );
        break;
    }

    grid.innerHTML = list.map(cardHtml).join("");
    emptyBox.classList.toggle("hidden", list.length > 0);
    resultCount.innerHTML = `Найдено: <b>${list.length}</b> из ${state.deputies.length}`;
  }

  function renderChips() {
    const all = [
      `<button class="chip ${state.party === "" ? "active" : ""}" data-party="">
         Все <span class="chip__count">${state.deputies.length}</span>
       </button>`,
    ];
    for (const p of state.parties) {
      all.push(`
        <button class="chip ${state.party === p.party ? "active" : ""}" data-party="${esc(p.party)}">
          <span class="chip__dot" style="background:${p.color}"></span>
          ${esc(p.party)} <span class="chip__count">${p.count}</span>
        </button>`);
    }
    chips.innerHTML = all.join("");
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
    const info = partyInfo.get(d.party);
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

  // events
  $("#search-form").addEventListener("submit", (e) => {
    e.preventDefault();
    state.query = $("#search-input").value.trim();
    render();
  });
  $("#search-input").addEventListener("input", (e) => {
    state.query = e.target.value.trim();
    render();
  });
  $("#sort-select").addEventListener("change", (e) => {
    state.sort = e.target.value;
    render();
  });
  chips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    state.party = chip.dataset.party;
    renderChips();
    render();
  });
  grid.addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (!card) return;
    const d = state.deputies.find((x) => x.id === card.dataset.id);
    if (d) openModal(d);
  });
  grid.addEventListener("keydown", (e) => {
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

  // init
  async function init() {
    try {
      const [candidates, parties] = await Promise.all([
        fetch("data/candidates.json").then((r) => r.json()),
        fetch("data/parties.json").then((r) => r.json()),
      ]);
      state.deputies = candidates;
      state.parties = parties;
      totalStat.textContent = `${candidates.length} кандидатов`;
      renderChips();
      render();
    } catch (err) {
      grid.innerHTML = `<div class="empty">Не удалось загрузить данные.</div>`;
      console.error(err);
    }
    try {
      const info = await fetch("data/parties_info.json").then((r) => r.json());
      for (const p of info.parties) partyInfo.set(p.party, p);
      render();
    } catch (err) {
      console.error(err);
    }
  }

  init();
})();
