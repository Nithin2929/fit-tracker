/* ==========================================================================
   FitTrack — workout-form.js
   Adds and removes optional exercise rows on the workout form.

   Server-side validation in app/routes/workouts.py is authoritative; this file
   only improves the form experience.
   ========================================================================== */

(function () {
  "use strict";

  const rows = document.querySelector("[data-exercise-rows]");
  const addButton = document.querySelector("[data-add-exercise]");
  const template = document.getElementById("exercise-row-template");
  if (!rows || !addButton || !template) return;

  const maximum = parseInt(addButton.getAttribute("data-max-rows"), 10) || 10;

  function updateAddButton() {
    const count = rows.querySelectorAll("[data-exercise-row]").length;
    addButton.disabled = count >= maximum;
  }

  addButton.addEventListener("click", () => {
    const count = rows.querySelectorAll("[data-exercise-row]").length;
    if (count >= maximum) return;
    const clone = template.content.cloneNode(true);
    rows.appendChild(clone);
    updateAddButton();
    const added = rows.querySelector("[data-exercise-row]:last-of-type select");
    if (added) added.focus();
  });

  rows.addEventListener("click", (event) => {
    const removeButton = event.target.closest("[data-remove-exercise]");
    if (!removeButton) return;
    const row = removeButton.closest("[data-exercise-row]");
    if (!row) return;
    row.remove();
    updateAddButton();
  });

  updateAddButton();
})();
