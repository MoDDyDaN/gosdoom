(function () {
  "use strict";

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let infoData = null;

  async function loadInfo() {
    if (infoData) return infoData;
    infoData = await fetch("data/parties_info.json").then((r) => r.json());
    return infoData;
  }

  function partyColor(name) {
    const info = (infoData && infoData.parties || []).find((p) => p.party === name);
    return info ? info.color : "#9ca3af";
  }

  function renderParties(container) {
    loadInfo().then((data) => {
      container.innerHTML = data.parties
        .map(
          (p) => `
      <article class="party-card">
        <div class="party-card__head">
          <img class="party-card__logo" src="${esc(p.logo)}" alt="" onerror="this.remove()">
          <h3>${esc(p.party)}</h3>
        </div>
        <div class="party-card__slogan">«${esc(p.slogan)}»</div>
        <p class="party-card__strategy"><b>Стратегия на срок:</b> ${esc(p.strategy)}</p>
        <div class="party-card__stances">
          <div class="party-card__stance"><b>К СВО:</b> ${esc(p.positions.svo.short)}</div>
          <div class="party-card__stance"><b>Отношение к СВО:</b> ${esc(p.positions.svo.full)}</div>
        </div>
      </article>`
        )
        .join("");
    }).catch(() => {
      container.innerHTML = `<div class="empty">Не удалось загрузить данные.</div>`;
    });
  }

  function renderParliament(container) {
    loadInfo().then((data) => {
      const total = 450;
      const rows = data.convocations
        .map((c) => {
          const segs = Object.entries(c.seats)
            .filter(([, v]) => v > 0)
            .map(
              ([name, v]) =>
                `<div class="chart-seg" style="width:${(v / total) * 100}%;background:${partyColor(name)}" title="${esc(name)}: ${v}"></div>`
            )
            .join("");
          return `
        <div class="chart-row">
          <div class="chart-row__label">${esc(c.name)}<span>${esc(c.years)}</span></div>
          <div class="chart-bar">${segs}</div>
        </div>`;
        })
        .join("");
      const allNames = [...new Set(data.convocations.flatMap((c) => Object.keys(c.seats)))].filter((n) => n !== "Прочие");
      const legendHtml = allNames
        .map((n) => `<span class="chart-legend__item"><i style="background:${partyColor(n)}"></i>${esc(n)}</span>`)
        .join("");
      container.innerHTML = `<div class="chart">${rows}</div><div class="chart-legend">${legendHtml}</div>`;
    }).catch(() => {
      container.innerHTML = `<div class="empty">Не удалось загрузить данные.</div>`;
    });
  }

  window.PartyInfo = { renderParties, renderParliament };
})();
