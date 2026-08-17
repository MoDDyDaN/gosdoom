(function () {
  "use strict";

  var player = document.getElementById("player");
  var playerCaption = document.getElementById("player-caption");
  var gridEl = document.getElementById("video-grid");
  var catalogTitle = document.getElementById("catalog-title");
  var speedBtn = document.querySelector(".speed-btn");
  var current = null;
  var SPEEDS = [1, 1.25, 1.5, 2];
  var speedIdx = 0;

  function speedLabel(rate) {
    return rate === 1 ? "1x" : (Math.round(rate * 100) / 100) + "x";
  }

  function setSpeed(idx) {
    speedIdx = ((idx % SPEEDS.length) + SPEEDS.length) % SPEEDS.length;
    var rate = SPEEDS[speedIdx];
    player.playbackRate = rate;
    speedBtn.textContent = speedLabel(rate);
    speedBtn.classList.toggle("speed-btn--active", rate !== 1);
  }

  if (speedBtn) {
    speedBtn.addEventListener("click", function () {
      setSpeed(speedIdx + 1);
    });
  }

  var volBtn = document.getElementById("vol-btn");
  var BOOSTS = [1, 1.5, 2];
  var boostIdx = 0;
  var audioCtx = null;
  var gainNode = null;

  function boostLevel(v) {
    return v === 1 ? "100%" : (Math.round(v * 100)) + "%";
  }

  function applyBoost() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      var src = audioCtx.createMediaElementSource(player);
      gainNode = audioCtx.createGain();
      src.connect(gainNode);
      gainNode.connect(audioCtx.destination);
    }
    gainNode.gain.value = BOOSTS[boostIdx];
    volBtn.textContent = boostLevel(BOOSTS[boostIdx]);
    volBtn.classList.toggle("speed-btn--active", BOOSTS[boostIdx] !== 1);
    volBtn.title = "Усиление громкости: " + volBtn.textContent;
  }

  if (volBtn) {
    volBtn.addEventListener("click", function () {
      boostIdx = (boostIdx + 1) % BOOSTS.length;
      applyBoost();
    });
  }


  function formatSize(bytes) {
    if (!bytes) return "";
    if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " МБ";
    if (bytes >= 1024) return (bytes / 1024).toFixed(1) + " КБ";
    return bytes + " Б";
  }

  function formatDuration(sec) {
    if (!sec) return "";
    sec = Math.round(sec);
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    var s = sec % 60;
    function pad(n) { return n < 10 ? "0" + n : "" + n; }
    if (h > 0) return h + ":" + pad(m) + ":" + pad(s);
    return m + ":" + pad(s);
  }

  function play(item, card) {
    current = item;
    player.poster = item.poster || "";
    player.src = item.url;
    player.load();
    player.play().catch(function () {});
    player.playbackRate = SPEEDS[speedIdx];
    playerCaption.textContent = item.title;
    document.title = (item.title ? item.title + " | " : "") + "Видео | ГосДума Маркет";
    document
      .querySelectorAll(".video-card")
      .forEach(function (el) { el.classList.remove("video-card--active"); });
    if (card) card.classList.add("video-card--active");
  }

  function card(item) {
    var el = document.createElement("div");
    el.className = "video-card";
    el.innerHTML =
      '<div class="video-card__media">' +
        '<img class="video-card__thumb" alt="">' +
        '<span class="video-card__duration"></span>' +
      '</div>' +
      '<div class="video-card__body">' +
        '<h3 class="video-card__title"></h3>' +
        '<div class="video-card__meta"></div>' +
      '</div>';
    var img = el.querySelector(".video-card__thumb");
    img.src = item.poster || "static/images/favicon.ico";
    img.alt = item.title;
    el.querySelector(".video-card__title").textContent = item.title;
    el.querySelector(".video-card__duration").textContent = formatDuration(item.duration);
    el.querySelector(".video-card__meta").textContent =
      formatSize(item.size) + (item.duration ? " • " + formatDuration(item.duration) : "");
    el.addEventListener("click", function () {
      play(item, el);
      player.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
    });
    return el;
  }

  function render(items) {
    catalogTitle.textContent = items.length ? "Каталог видео (" + items.length + ")" : "Каталог видео";
    videoGridClear();
    if (!items.length) {
      showEmpty();
      return;
    }
    items.forEach(function (item) {
      gridEl.appendChild(card(item));
    });
    // autoplay первого
    var firstCard = gridEl.querySelector(".video-card");
    play(items[0], firstCard);
  }

  function videoGridClear() {
    gridEl.innerHTML = "";
  }

  function showEmpty() {
    gridEl.innerHTML =
      '<div class="video-empty">Видео ещё не загружены. Добавьте файл в папку <code>static/videos/</code>.</div>';
  }

  showEmpty();
})();