// Forms post to the URL in data-endpoint. Endpoints are TODO (see tools/build.py and README).
// While an endpoint is empty, the form validates input but tells the visitor it is not connected yet.
document.querySelectorAll("form[data-endpoint]").forEach(function (f) {
  f.addEventListener("submit", async function (ev) {
    ev.preventDefault();
    var s = f.querySelector(".form-status"); s.className = "form-status";
    if (!f.checkValidity()) { f.reportValidity(); s.textContent = "Please fill in the required fields."; s.classList.add("err"); return; }
    if (f.querySelector("[name=_gotcha]").value) return;
    var ep = f.dataset.endpoint;
    if (!ep) { s.textContent = "This form isn't connected yet. We're launching soon; please check back shortly."; s.classList.add("err"); return; }
    s.textContent = "Sending…";
    try {
      var r = await fetch(ep, { method: "POST", body: new FormData(f), headers: { Accept: "application/json" } });
      if (!r.ok) throw new Error(r.status);
      f.reset(); s.textContent = "Thanks! We got it and will reply by email."; s.classList.add("ok");
    } catch (e) { s.textContent = "Something went wrong. Please try again in a moment."; s.classList.add("err"); }
  });
});
