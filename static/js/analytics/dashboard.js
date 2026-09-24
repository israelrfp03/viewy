(function () {
  "use strict";

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    return JSON.parse(el.textContent);
  }

  var COLORS = {
    ink: "#0D0E12",
    brand: "#0038BE",
    brand300: "#7392DB",
    brand200: "#A6B9E8",
    text: "#6B6D73",
  };

  var TYPE_COLORS = { Película: COLORS.ink, Serie: COLORS.brand300, Anime: COLORS.brand };
  var TYPE_COLORS_BY_KEY = { movie: COLORS.ink, series: COLORS.brand300, anime: COLORS.brand };

  if (window.Chart) {
    window.Chart.defaults.font.family = "Geist, ui-sans-serif, system-ui, sans-serif";
    window.Chart.defaults.color = COLORS.text;
  }

  function axisNoGrid() {
    return { ticks: { color: COLORS.text }, grid: { display: false }, border: { display: false } };
  }

  function commonScales() {
    return {
      x: axisNoGrid(),
      y: Object.assign({ beginAtZero: true }, axisNoGrid()),
    };
  }

  function commonOptions(overrides) {
    var base = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: "#0D0E12", titleColor: "#ffffff", bodyColor: "#DCE4FA", padding: 10, cornerRadius: 6 },
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
    return TYPE_COLORS[label] || COLORS.brand300;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var monthly = readJSON("chart-data-monthly-activity");
    if (monthly) {
      renderChart("chart-monthly-activity", {
        type: "bar",
        data: {
          labels: monthly.labels,
          datasets: [{ label: "Terminados", data: monthly.data, backgroundColor: COLORS.brand, borderRadius: 3 }],
        },
        options: commonOptions({ scales: commonScales() }),
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
              borderColor: "#FFFFFF",
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
          datasets: [{ label: "Elementos", data: ratingDistribution.data, backgroundColor: COLORS.brand, borderRadius: 3 }],
        },
        options: commonOptions({ scales: commonScales() }),
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
              borderRadius: 3,
            },
          ],
        },
        options: commonOptions({
          indexAxis: "y",
          scales: {
            x: Object.assign({ beginAtZero: true, max: 10 }, axisNoGrid()),
            y: axisNoGrid(),
          },
        }),
      });
    }

    var yearlyActivity = readJSON("chart-data-yearly-activity");
    if (yearlyActivity) {
      renderChart("chart-yearly-activity", {
        type: "bar",
        data: {
          labels: yearlyActivity.labels,
          datasets: [{ label: "Terminados", data: yearlyActivity.data, backgroundColor: COLORS.brand, borderRadius: 3 }],
        },
        options: commonOptions({ scales: commonScales() }),
      });
    }

    var typeOverTime = readJSON("chart-data-type-over-time");
    if (typeOverTime) {
      renderChart("chart-type-over-time", {
        type: "bar",
        data: {
          labels: typeOverTime.labels,
          datasets: [
            { label: "Película", data: typeOverTime.datasets.movie, backgroundColor: TYPE_COLORS_BY_KEY.movie, borderRadius: 3 },
            { label: "Serie", data: typeOverTime.datasets.series, backgroundColor: TYPE_COLORS_BY_KEY.series, borderRadius: 3 },
            { label: "Anime", data: typeOverTime.datasets.anime, backgroundColor: TYPE_COLORS_BY_KEY.anime, borderRadius: 3 },
          ],
        },
        options: commonOptions({
          scales: {
            x: Object.assign({ stacked: true }, axisNoGrid()),
            y: Object.assign({ stacked: true, beginAtZero: true }, axisNoGrid()),
          },
        }),
      });
    }
  });
})();
