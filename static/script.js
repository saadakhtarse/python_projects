document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  const postcodeInput = document.querySelector("input[name='postcode']");
  const resultSection = document.querySelector(".result-container");

  // Autofocus the postcode field on page load
  if (postcodeInput) {
    postcodeInput.focus();
  }

  // Smooth scroll to results on form submission
  form.addEventListener("submit", function () {
    setTimeout(() => {
      const result = document.querySelector(".result-container");
      if (result) {
        result.scrollIntoView({ behavior: "smooth" });
      }
    }, 500); // wait for results to load
  });

  // Optional: alert if postcode is empty or only whitespace
  form.addEventListener("submit", function (e) {
    if (postcodeInput && postcodeInput.value.trim() === "") {
      alert("Please enter a valid postcode.");
      e.preventDefault();
      postcodeInput.focus();
    }
  });
});
