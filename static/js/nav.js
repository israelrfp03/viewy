(function () {
  "use strict";

  function initScrollBorder() {
    var navbars = document.querySelectorAll("[data-navbar]");
    if (!navbars.length) return;

    function update() {
      var scrolled = window.scrollY > 4;
      navbars.forEach(function (el) {
        el.classList.toggle("border-line", scrolled);
        el.classList.toggle("shadow-sm", scrolled);
        el.classList.toggle("border-transparent", !scrolled);
      });
    }

    update();
    window.addEventListener("scroll", update, { passive: true });
  }

  function initDropdowns() {
    document.querySelectorAll("[data-dropdown]").forEach(function (wrapper) {
      var trigger = wrapper.querySelector("[data-dropdown-trigger]");
      var panel = wrapper.querySelector("[data-dropdown-panel]");
      if (!trigger || !panel) return;

      trigger.addEventListener("click", function (event) {
        event.stopPropagation();
        panel.classList.toggle("hidden");
      });
    });

    document.addEventListener("click", function (event) {
      document.querySelectorAll("[data-dropdown]").forEach(function (wrapper) {
        if (!wrapper.contains(event.target)) {
          var panel = wrapper.querySelector("[data-dropdown-panel]");
          if (panel) panel.classList.add("hidden");
        }
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      document.querySelectorAll("[data-dropdown-panel]").forEach(function (panel) {
        panel.classList.add("hidden");
      });
    });
  }

  function initSheets() {
    var CLOSE_DELAY = 220;

    document.querySelectorAll("[data-sheet-trigger]").forEach(function (trigger) {
      var sheet = document.querySelector(trigger.getAttribute("data-sheet-trigger"));
      if (!sheet) return;

      var backdrop = sheet.querySelector("[data-sheet-backdrop]");
      var panel = sheet.querySelector("[data-sheet-panel]");

      function open() {
        sheet.classList.remove("hidden");
        window.requestAnimationFrame(function () {
          if (backdrop) backdrop.classList.remove("opacity-0");
          if (panel) panel.classList.remove("translate-y-full");
        });
      }

      function close() {
        if (backdrop) backdrop.classList.add("opacity-0");
        if (panel) panel.classList.add("translate-y-full");
        window.setTimeout(function () {
          sheet.classList.add("hidden");
        }, CLOSE_DELAY);
      }

      trigger.addEventListener("click", open);

      sheet.querySelectorAll("[data-sheet-close]").forEach(function (closeEl) {
        closeEl.addEventListener("click", close);
      });
    });
  }

  function initSearchShortcut() {
    var input = document.querySelector("[data-search-input]");
    if (!input) return;

    document.addEventListener("keydown", function (event) {
      var tag = document.activeElement ? document.activeElement.tagName : "";
      if (event.key === "/" && tag !== "INPUT" && tag !== "TEXTAREA") {
        event.preventDefault();
        input.focus();
      }
    });
  }

  function initToastAutoClose() {
    document.querySelectorAll("[data-toast]").forEach(function (toast) {
      window.setTimeout(function () {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(12px)";
        window.setTimeout(function () {
          toast.remove();
        }, 300);
      }, 4000);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initScrollBorder();
    initDropdowns();
    initSheets();
    initSearchShortcut();
    initToastAutoClose();
  });
})();
