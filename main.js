// ---------------------------------------------------------------------------
// Geolocation: capture the customer's GPS once and store it in a cookie so
// every server-rendered page can compute real distances. (Feature #2)
// ---------------------------------------------------------------------------
(function detectLocation() {
  function setLoc(lat, lng) {
    document.cookie = `lat=${lat};path=/;max-age=86400`;
    document.cookie = `lng=${lng};path=/;max-age=86400`;
    document.querySelectorAll("[data-loc-status]").forEach(el => {
      el.innerHTML = `<i class="bi bi-geo-alt-fill text-success"></i> Using your location`;
    });
  }
  // Only ask once per session.
  if (!document.cookie.includes("lat=") && navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      p => { setLoc(p.coords.latitude.toFixed(5), p.coords.longitude.toFixed(5));
             if (document.body.dataset.reloadOnLoc) location.reload(); },
      () => {}, { timeout: 6000 }
    );
  }
  // Manual "use my location" buttons
  document.querySelectorAll("[data-detect-loc]").forEach(btn => {
    btn.addEventListener("click", () => {
      navigator.geolocation.getCurrentPosition(p => {
        setLoc(p.coords.latitude.toFixed(5), p.coords.longitude.toFixed(5));
        location.reload();
      });
    });
  });
})();

// Fill hidden lat/lng inputs on the shop registration form from the browser.
function pickMyCoords(latId, lngId) {
  navigator.geolocation.getCurrentPosition(p => {
    document.getElementById(latId).value = p.coords.latitude.toFixed(6);
    document.getElementById(lngId).value = p.coords.longitude.toFixed(6);
    alert("Captured GPS coordinates from your device.");
  });
}

// Render star rating helper
function starHtml(rating) {
  let full = Math.floor(rating), html = "";
  for (let i = 0; i < 5; i++) html += `<i class="bi bi-star${i < full ? '-fill' : ''}"></i>`;
  return `<span class="stars">${html}</span>`;
}
