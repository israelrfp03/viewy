(function () {
  "use strict";

  function initScrollReveal() {
    var elements = document.querySelectorAll("[data-reveal]");
    if (!elements.length) return;

    if (!("IntersectionObserver" in window)) {
      elements.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    elements.forEach(function (el) {
      observer.observe(el);
    });
  }

  function animateCounter(el) {
    var target = parseFloat(el.getAttribute("data-counter"));
    if (isNaN(target)) return;

    var decimals = el.getAttribute("data-counter-decimals")
      ? parseInt(el.getAttribute("data-counter-decimals"), 10)
      : 0;
    var duration = 900;
    var start = null;

    function step(timestamp) {
      if (!start) start = timestamp;
      var progress = Math.min((timestamp - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var value = target * eased;
      el.textContent = decimals ? value.toFixed(decimals) : Math.round(value);

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        el.textContent = decimals ? target.toFixed(decimals) : target;
      }
    }

    window.requestAnimationFrame(step);
  }

  function initCounters() {
    var counters = document.querySelectorAll("[data-counter]");
    if (!counters.length) return;

    if (
      !("IntersectionObserver" in window) ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );

    counters.forEach(function (el) {
      observer.observe(el);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initScrollReveal();
    initCounters();
  });
})();
