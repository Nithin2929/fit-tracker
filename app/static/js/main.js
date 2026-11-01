/* ==========================================================================
   FitTrack — main.js
   Shared behaviour for every page:
   1. Sticky header shadow
   2. Responsive navigation menu
   3. Today's date in the dashboard preview
   4. Footer year
   5. Scroll reveal animation
   6. Animated number counters
   ========================================================================== */

(function () {
  "use strict";

  // Enables the reveal styles only when JavaScript is available.
  document.documentElement.classList.add("js");

  /* 1. Sticky header shadow ---------------------------------------------- */
  const header = document.querySelector("[data-header]");

  function updateHeader() {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  }

  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });

  /* 2. Responsive navigation menu ---------------------------------------- */
  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-nav]");

  function setMenu(open) {
    if (!navToggle || !nav) return;
    navToggle.setAttribute("aria-expanded", String(open));
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
  }

  if (navToggle && nav) {
    navToggle.addEventListener("click", function () {
      setMenu(navToggle.getAttribute("aria-expanded") !== "true");
    });

    // Close the menu after clicking a link.
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setMenu(false);
      });
    });

    // Close with the Escape key.
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setMenu(false);
    });

    // Close when the window becomes wide enough for the desktop menu.
    window.addEventListener("resize", function () {
      if (window.innerWidth > 1020) setMenu(false);
    });
  }

  /* 3. Today's date ------------------------------------------------------ */
  const todayElement = document.querySelector("[data-today]");

  if (todayElement) {
    todayElement.textContent = new Date().toLocaleDateString("en-GB", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
  }

  /* 4. Footer year ------------------------------------------------------- */
  document.querySelectorAll("[data-year]").forEach(function (element) {
    element.textContent = String(new Date().getFullYear());
  });

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* 5. Scroll reveal ----------------------------------------------------- */
  const revealElements = document.querySelectorAll(".reveal");

  if (revealElements.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      revealElements.forEach(function (element) {
        element.classList.add("is-visible");
      });
    } else {
      const revealObserver = new IntersectionObserver(
        function (entries, observer) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
      );

      revealElements.forEach(function (element) {
        revealObserver.observe(element);
      });
    }
  }

  /* 6. Animated number counters ----------------------------------------- */
  const counters = document.querySelectorAll("[data-count]");
  const numberFormat = new Intl.NumberFormat("en-US");

  function setFinalValue(element) {
    const target = Number(element.dataset.count || 0);
    const suffix = element.dataset.suffix || "";
    element.textContent = numberFormat.format(target) + suffix;
  }

  function animateCounter(element) {
    const target = Number(element.dataset.count || 0);
    const suffix = element.dataset.suffix || "";
    const startTime = performance.now();
    const duration = 1100;

    function tick(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      element.textContent = numberFormat.format(Math.round(target * eased)) + suffix;

      if (progress < 1) {
        window.requestAnimationFrame(tick);
      }
    }

    window.requestAnimationFrame(tick);
  }

  if (counters.length) {
    if (reduceMotion || !("IntersectionObserver" in window)) {
      counters.forEach(setFinalValue);
    } else {
      const counterObserver = new IntersectionObserver(
        function (entries, observer) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              animateCounter(entry.target);
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.6 }
      );

      counters.forEach(function (counter) {
        counterObserver.observe(counter);
      });
    }
  }
})();
