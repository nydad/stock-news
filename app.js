/**
 * Stock Daily Digest v1.0
 * Market overview + news tabs, dark financial terminal theme
 */
(function () {
  "use strict";

  var dates = [];
  var currentDate = "";
  var currentTab = "overview";
  var cache = {};

  var CAT_ICONS = {
    market: "\u{1F4C8}", economy: "\u{1F3E6}", policy: "\u{1F3DB}\uFE0F",
    earnings: "\u{1F4CA}", forex: "\u{1F4B1}", commodity: "\u{26CF}\uFE0F",
    crypto: "\u{1FA99}", geopolitics: "\u{1F30D}"
  };

  var INSIGHT_KR = { bullish: "\uAC15\uC138", bearish: "\uC57D\uC138", neutral: "\uC911\uB9BD", alert: "\uC8FC\uC758" };

  var MARKET_TITLES = {
    indices: "\uC8FC\uC694 \uC9C0\uC218", futures: "\uC120\uBB3C", volatility: "\uBCC0\uB3D9\uC131",
    forex: "\uD658\uC728", commodities: "\uC6D0\uC790\uC7AC", crypto: "\uC554\uD638\uD654\uD3D0", bonds: "\uCC44\uAD8C"
  };

  // --- Init ---
  async function init() {
    setupTabs();
    try {
      var r = await fetch("./data/index.json");
      if (!r.ok) throw 0;
      var d = await r.json();
      dates = d.dates || [];
      if (!dates.length) return showEmpty();
      renderDateBar();
      selectDate(dates[0]);
    } catch (e) { showEmpty(); }
  }

  // --- Tabs ---
  function setupTabs() {
    document.querySelectorAll(".tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (btn.dataset.tab === currentTab) return;
        document.querySelectorAll(".tab").forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        currentTab = btn.dataset.tab;
        if (cache[currentDate]) render(cache[currentDate]);
      });
    });
  }

  // --- Date Bar ---
  function renderDateBar() {
    var el = document.getElementById("date-scroll");
    if (!el) return;
    el.innerHTML = dates.map(function (d) {
      var parts = d.split("-");
      var label = parseInt(parts[1]) + "/" + parseInt(parts[2]);
      var dayNames = ["\uC77C", "\uC6D4", "\uD654", "\uC218", "\uBAA9", "\uAE08", "\uD1A0"];
      var dt = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
      var day = dayNames[dt.getDay()];
      return '<button class="date-chip" data-date="' + d + '">' + label + ' ' + day + '</button>';
    }).join("");
    el.addEventListener("click", function (e) {
      var chip = e.target.closest(".date-chip");
      if (chip) selectDate(chip.dataset.date);
    });
  }

  function selectDate(date) {
    currentDate = date;
    document.querySelectorAll(".date-chip").forEach(function (c) {
      c.classList.toggle("active", c.dataset.date === date);
    });
    loadDigest(date);
  }

  async function loadDigest(date) {
    show("loading"); hide("digest"); hide("empty-state");
    if (cache[date]) { render(cache[date]); return; }
    try {
      var r = await fetch("./data/" + date + ".json");
      if (!r.ok) throw 0;
      var d = await r.json();
      cache[date] = d;
      render(d);
    } catch (e) { showError(date); }
  }

  // --- Render ---
  function render(d) {
    if (currentTab === "overview") renderOverview(d);
    else renderNews(d);
  }

  function renderOverview(d) {
    var el = document.getElementById("digest");
    if (!el) return;
    var dateStr = fmtDate(d.date);
    var h = "";

    // Market Briefing
    if (d.market_briefing) {
      h += '<section class="briefing fade-in">' +
        '<p class="section-label">\uC2DC\uD669 \uBE0C\uB9AC\uD551</p>' +
        '<div class="editorial">' + esc(d.market_briefing) + '</div>' +
        '<p class="stats">' + dateStr + ' \u00B7 ' + (d.total_articles || 0) + '\uAC1C \uAE30\uC0AC</p>' +
        renderTrends(d.trends) +
        '</section><hr class="divider">';
    }

    // Market Data
    if (d.market_data) {
      h += '<section class="fade-in"><p class="section-label">\uC2DC\uC7A5 \uB370\uC774\uD130</p>';
      var order = ["indices", "futures", "volatility", "forex", "commodities", "crypto", "bonds"];
      for (var oi = 0; oi < order.length; oi++) {
        var cat = order[oi];
        var items = d.market_data[cat];
        if (items && items.length) {
          h += '<div class="market-section">' +
            '<div class="market-section-title">' + (MARKET_TITLES[cat] || cat) + '</div>' +
            '<div class="market-grid">';
          for (var mi = 0; mi < items.length; mi++) {
            h += renderMarketCard(items[mi]);
          }
          h += '</div></div>';
        }
      }
      h += '</section><hr class="divider">';
    }

    // Fear & Greed
    if (d.fear_greed && d.fear_greed.score) {
      var fg = d.fear_greed;
      var fgColor = fg.score >= 60 ? "var(--green)" : fg.score <= 40 ? "var(--red)" : "var(--yellow)";
      h += '<section class="fade-in">' +
        '<p class="section-label">Fear & Greed Index</p>' +
        '<div class="fg-card">' +
        '<div class="fg-score" style="color:' + fgColor + '">' + fg.score + '</div>' +
        '<div>' +
        '<div class="fg-label">CNN Fear & Greed</div>' +
        '<div class="fg-rating">' + esc(fg.rating) + '</div>' +
        '<div class="fg-prev">\uC804\uC77C: ' + fg.previous_close + '</div>' +
        '</div></div></section><hr class="divider">';
    }

    // Key Insights
    if (d.key_insights && d.key_insights.length) {
      h += '<section class="fade-in"><p class="section-label">\uD575\uC2EC \uC778\uC0AC\uC774\uD2B8</p>' +
        '<div class="insight-list">';
      for (var ii = 0; ii < d.key_insights.length; ii++) {
        var ins = d.key_insights[ii];
        var typeCls = ins.type || "neutral";
        var typeLabel = INSIGHT_KR[typeCls] || typeCls;
        h += '<div class="insight-item">' +
          '<span class="insight-type ' + typeCls + '">' + typeLabel + '</span>' +
          '<div class="insight-body">' +
          '<div class="insight-title">' + esc(ins.title) + '</div>' +
          '<div class="insight-detail">' + esc(ins.detail) + '</div>' +
          '</div></div>';
      }
      h += '</div></section><hr class="divider">';
    }

    // Commentary
    if (d.forex_commentary || d.commodity_commentary) {
      h += '<section class="fade-in">';
      if (d.forex_commentary) {
        h += '<div class="commentary-card">' +
          '<div class="commentary-title">\uD658\uC728 \uCF54\uBA58\uD2B8</div>' +
          '<div class="commentary-text">' + esc(d.forex_commentary) + '</div></div>';
      }
      if (d.commodity_commentary) {
        h += '<div class="commentary-card">' +
          '<div class="commentary-title">\uC6D0\uC790\uC7AC \uCF54\uBA58\uD2B8</div>' +
          '<div class="commentary-text">' + esc(d.commodity_commentary) + '</div></div>';
      }
      h += '</section><hr class="divider">';
    }

    // Outlook
    if (d.outlook) {
      h += '<section class="fade-in">' +
        '<p class="section-label">\uC624\uB298\uC758 \uC804\uB9DD</p>' +
        '<div class="outlook-card">' +
        '<div class="outlook-text">' + esc(d.outlook) + '</div>' +
        '</div></section>';
    }

    if (!h) {
      h = '<div class="error-state fade-in"><h2>\uB370\uC774\uD130\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4</h2><p>' + dateStr + '</p></div>';
    }

    el.innerHTML = h;
    hide("loading"); hide("empty-state"); show("digest");
  }

  function renderNews(d) {
    var el = document.getElementById("digest");
    if (!el) return;
    var dateStr = fmtDate(d.date);
    var h = "";

    if (d.categories && d.categories.length) {
      h += '<section class="fade-in" style="padding-top:28px">';
      for (var ci = 0; ci < d.categories.length; ci++) {
        var cat = d.categories[ci];
        var icon = CAT_ICONS[cat.id] || "\u{1F4F0}";
        h += '<div class="category-section">' +
          '<div class="category-header">' +
          '<span class="category-icon">' + icon + '</span>' +
          '<span class="category-name">' + esc(cat.name) + '</span>' +
          '<span class="category-count">' + cat.articles.length + '</span>' +
          '</div>';
        for (var ai = 0; ai < cat.articles.length; ai++) {
          h += renderArticle(cat.articles[ai]);
        }
        h += '</div>';
      }
      h += '</section>';
    } else {
      h = '<div class="error-state fade-in"><h2>\uC774 \uB0A0\uC9DC\uC5D0 \uD574\uB2F9\uD558\uB294 \uAE30\uC0AC\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4</h2><p>' + dateStr + '</p></div>';
    }

    el.innerHTML = h;
    hide("loading"); hide("empty-state"); show("digest");
  }

  function renderMarketCard(item) {
    var dir = item.change > 0 ? "up" : item.change < 0 ? "down" : "flat";
    var sign = item.change > 0 ? "+" : "";
    var arrow = item.change > 0 ? "\u25B2" : item.change < 0 ? "\u25BC" : "";
    return '<div class="market-card">' +
      '<div class="market-name">' + esc(item.name) + '</div>' +
      '<div class="market-price">' + fmtNum(item.price) + '</div>' +
      '<div class="market-change ' + dir + '">' +
      arrow + ' ' + sign + fmtNum(item.change) + ' (' + sign + item.change_pct + '%)' +
      '</div></div>';
  }

  function renderArticle(a) {
    var t = ago(a.published);
    var imp = a.importance === "high" ? '<span class="article-important">\uC8FC\uC694</span>' : "";
    var tags = "";
    if (a.tags && a.tags.length) {
      tags = '<div class="article-tags">';
      for (var i = 0; i < Math.min(a.tags.length, 4); i++) {
        tags += '<span class="article-tag">' + esc(a.tags[i]) + '</span>';
      }
      tags += '</div>';
    }
    return '<article class="article">' +
      '<h3 class="article-title"><a href="' + attr(a.url) + '" target="_blank" rel="noopener noreferrer">' + esc(a.title) + '</a></h3>' +
      '<div class="article-meta"><span class="article-source">' + esc(a.source) + '</span><span>\u00B7</span><span>' + t + '</span>' + imp + '</div>' +
      '<p class="article-summary">' + esc(a.summary || "") + '</p>' + tags + '</article>';
  }

  function renderTrends(trends) {
    if (!trends || !trends.length) return "";
    var h = '<div class="trends"><span class="trend-label">\uD0A4\uC6CC\uB4DC</span>';
    for (var i = 0; i < trends.length; i++) {
      h += '<span class="trend-item">' + esc(trends[i]) + '</span>';
    }
    return h + '</div>';
  }

  // --- Helpers ---
  function fmtDate(s) {
    var p = s.split("-").map(Number);
    var dt = new Date(p[0], p[1] - 1, p[2]);
    var day = ["\uC77C", "\uC6D4", "\uD654", "\uC218", "\uBAA9", "\uAE08", "\uD1A0"][dt.getDay()];
    return p[0] + "\uB144 " + p[1] + "\uC6D4 " + p[2] + "\uC77C " + day + "\uC694\uC77C";
  }

  function fmtNum(n) {
    if (typeof n !== "number") return String(n);
    if (Math.abs(n) >= 1000) return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (Math.abs(n) < 1) return n.toFixed(4);
    return n.toFixed(2);
  }

  function ago(iso) {
    if (!iso) return "";
    try {
      var ms = Date.now() - new Date(iso).getTime();
      var h = Math.floor(ms / 3600000);
      if (h < 1) return "\uBC29\uAE08";
      if (h < 24) return h + "\uC2DC\uAC04 \uC804";
      return Math.floor(h / 24) + "\uC77C \uC804";
    } catch (e) { return ""; }
  }

  function esc(s) {
    if (!s) return "";
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function attr(s) { return (s || "").replace(/"/g, "&quot;"); }

  function show(id) { var el = document.getElementById(id); if (el) el.classList.remove("hidden"); }
  function hide(id) { var el = document.getElementById(id); if (el) el.classList.add("hidden"); }

  function showEmpty() { hide("loading"); hide("digest"); show("empty-state"); }
  function showError(date) {
    var el = document.getElementById("digest");
    if (el) {
      el.innerHTML = '<div class="error-state fade-in"><h2>\uD574\uB2F9 \uB0A0\uC9DC\uC758 \uB370\uC774\uD130\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4</h2><p>' + fmtDate(date) + '</p></div>';
    }
    hide("loading"); hide("empty-state"); show("digest");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
