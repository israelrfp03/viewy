(function () {
  "use strict";

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    return JSON.parse(el.textContent);
  }

  var COLORS = {
    pink: "#ec4899",
    amber: "#fbbf24",
    blue: "#60a5fa",
    emerald: "#34d399",
    purple: "#a78bfa",
    grid: "rgba(255, 255, 255, 0.06)",
    text: "#a1a1aa",
  };

  var TYPE_COLORS = { Película: COLORS.blue, Serie: COLORS.emerald, Anime: COLORS.pink };
  var TYPE_COLORS_BY_KEY = { movie: COLORS.blue, series: COLORS.emerald, anime: COLORS.pink };

  function commonScales() {
    return {
      x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid } },
      y: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, beginAtZero: true },
    };
  }

  function commonOptions(overrides) {
    var base = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: COLORS.text } },
        tooltip: { backgroundColor: "#18181b", titleColor: "#ffffff", bodyColor: "#d4d4d8" },
      },
    };
    return Object.assign(base, overrides || {});
  }

  function renderChart(canvasId, config) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    // eslint-disable-next-line no-undef
    new Chart(canvas.getContext("2d"), config);
  }

  function colorFor(label) {
    return TYPE_COLORS[label] || COLORS.purple;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var monthly = readJSON("chart-data-monthly-activity");
    if (monthly) {
      renderChart("chart-monthly-activity", {
        type: "bar",
        data: {
          labels: monthly.labels,
          datasets: [
            { label: "Terminados", data: monthly.data, backgroundColor: COLORS.pink, borderRadius: 4 },
          ],
        },
        options: commonOptions({ scales: commonScales(), plugins: { legend: { display: false } } }),
      });
    }

    var typeBreakdown = readJSON("chart-data-type-breakdown");
    if (typeBreakdown) {
      renderChart("chart-type-breakdown", {
        type: "doughnut",
        data: {
          labels: typeBreakdown.labels,
          datasets: [
            {
              data: typeBreakdown.data,
              backgroundColor: typeBreakdown.labels.map(colorFor),
              borderColor: "#09090b",
              borderWidth: 2,
            },
          ],
        },
        options: commonOptions(),
      });
    }

    var ratingDistribution = readJSON("chart-data-rating-distribution");
    if (ratingDistribution) {
      renderChart("chart-rating-distribution", {
        type: "bar",
        data: {
          labels: ratingDistribution.labels,
          datasets: [
            { label: "Elementos", data: ratingDistribution.data, backgroundColor: COLORS.amber, borderRadius: 4 },
          ],
        },
        options: commonOptions({ scales: commonScales(), plugins: { legend: { display: false } } }),
      });
    }

    var ratingsByType = readJSON("chart-data-ratings-by-type");
    if (ratingsByType) {
      renderChart("chart-ratings-by-type", {
        type: "bar",
        data: {
          labels: ratingsByType.labels,
          datasets: [
            {
              label: "Rating medio",
              data: ratingsByType.data,
              backgroundColor: ratingsByType.labels.map(colorFor),
              borderRadius: 4,
            },
          ],
        },
        options: commonOptions({
          indexAxis: "y",
          scales: {
            x: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, beginAtZero: true, max: 10 },
            y: { ticks: { color: COLORS.text }, grid: { display: false } },
          },
          plugins: { legend: { display: false } },
        }),
      });
    }

    var yearlyActivity = readJSON("chart-data-yearly-activity");
    if (yearlyActivity) {
      renderChart("chart-yearly-activity", {
        type: "bar",
        data: {
          labels: yearlyActivity.labels,
          datasets: [
            { label: "Terminados", data: yearlyActivity.data, backgroundColor: COLORS.emerald, borderRadius: 4 },
          ],
        },
        options: commonOptions({ scales: commonScales(), plugins: { legend: { display: false } } }),
      });
    }

    var typeOverTime = readJSON("chart-data-type-over-time");
    if (typeOverTime) {
      renderChart("chart-type-over-time", {
        type: "bar",
        data: {
          labels: typeOverTime.labels,
          datasets: [
            { label: "Película", data: typeOverTime.datasets.movie, backgroundColor: TYPE_COLORS_BY_KEY.movie },
            { label: "Serie", data: typeOverTime.datasets.series, backgroundColor: TYPE_COLORS_BY_KEY.series },
            { label: "Anime", data: typeOverTime.datasets.anime, backgroundColor: TYPE_COLORS_BY_KEY.anime },
          ],
        },
        options: commonOptions({
          scales: {
            x: { stacked: true, ticks: { color: COLORS.text }, grid: { color: COLORS.grid } },
            y: { stacked: true, ticks: { color: COLORS.text }, grid: { color: COLORS.grid }, beginAtZero: true },
          },
        }),
      });
    }
  });
})();
