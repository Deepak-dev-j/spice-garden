document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss flash messages after 4 seconds.
  document.querySelectorAll(".alert").forEach(function (el) {
    setTimeout(function () {
      if (window.bootstrap) bootstrap.Alert.getOrCreateInstance(el).close();
    }, 4000);
  });

  // Prevent double-submitting the checkout form.
  document.querySelectorAll("form.prevent-double").forEach(function (form) {
    form.addEventListener("submit", function () {
      const button = form.querySelector("button[type=submit]");
      if (button) button.disabled = true;
    });
  });
});
