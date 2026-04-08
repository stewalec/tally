/* Tally – main.js */

/* ── Theme toggling ──────────────────────────────────────── */

var THEME_KEY = "tally-theme";
var MODES = ["system", "light", "dark"];
var ICONS = { system: "\u25D0", light: "\u2600", dark: "\u263E" };   // ◐  ☀  ☾
var LABELS = { system: "System", light: "Light", dark: "Dark" };

function getStoredPref() {
  return localStorage.getItem(THEME_KEY) || "system";
}

function resolveTheme(pref) {
  if (pref === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return pref;
}

function applyTheme(pref) {
  document.documentElement.dataset.theme = resolveTheme(pref);
  localStorage.setItem(THEME_KEY, pref);
  updateToggleButtons(pref);
}

function updateToggleButtons(pref) {
  document.querySelectorAll(".theme-toggle").forEach(function (btn) {
    btn.textContent = ICONS[pref];
    btn.title = "Theme: " + LABELS[pref];
  });
}

// Listen for OS theme changes when set to "system"
window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", function () {
    if (getStoredPref() === "system") {
      applyTheme("system");
    }
  });

/* ── DOMContentLoaded ────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", function () {
  // Initialise theme toggle buttons
  var pref = getStoredPref();
  updateToggleButtons(pref);

  document.querySelectorAll(".theme-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var current = getStoredPref();
      var next = MODES[(MODES.indexOf(current) + 1) % MODES.length];
      applyTheme(next);
    });
  });

  // Auto-focus the OTP input on the verify page
  var codeInput = document.getElementById("id_code");
  if (codeInput) {
    codeInput.focus();
    // Auto-submit when 6 digits are entered
    codeInput.addEventListener("input", function () {
      if (codeInput.value.length === 6 && /^\d{6}$/.test(codeInput.value)) {
        codeInput.closest("form").submit();
      }
    });
  }

  // Auto-focus phone number field
  var phoneInput = document.getElementById("id_phone_number");
  if (phoneInput) {
    phoneInput.focus();
  }

  // Date filter: set sensible max dates
  var dateTo = document.querySelector('input[name="to"]');
  var dateFrom = document.querySelector('input[name="from"]');
  if (dateTo && !dateTo.value) {
    dateTo.value = new Date().toISOString().slice(0, 10);
  }
  if (dateFrom) {
    dateFrom.addEventListener("change", function () {
      if (dateTo && dateFrom.value > dateTo.value) {
        dateTo.value = dateFrom.value;
      }
    });
  }
});
