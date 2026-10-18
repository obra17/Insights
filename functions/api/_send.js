// Shared helper: validate a form submission and email it to info@ via Resend.
const TO = "info@obrainsights.com";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json" } });
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@]{2,}$/;

export async function handle(request, env, { label, fields, required, confirm }) {
  let data;
  try { data = Object.fromEntries(await request.formData()); } catch { return json({ ok: false, error: "Bad request" }, 400); }
  if (data._gotcha) return json({ ok: true }); // honeypot: pretend success for bots
  const clean = {};
  for (const k of fields) clean[k] = String(data[k] ?? "").trim().slice(0, k === "message" || k === "problem" ? 5000 : 500);
  for (const k of required) if (!clean[k]) return json({ ok: false, error: `Missing ${k}` }, 400);
  if (!EMAIL.test(clean.email)) return json({ ok: false, error: "Invalid email" }, 400);
  if (!env.RESEND_API_KEY) return json({ ok: false, error: "Email not configured" }, 503);
  const rows = fields.map((k) => `<tr><td style="padding:4px 12px 4px 0;color:#666">${esc(k)}</td><td style="padding:4px 0;white-space:pre-wrap">${esc(clean[k] || "—")}</td></tr>`).join("");
  const text = fields.map((k) => `${k}: ${clean[k] || "-"}`).join("\n");
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: env.FORM_FROM || "Obrainsights Forms <onboarding@resend.dev>",
      to: [TO],
      reply_to: clean.email,
      subject: `[${label}] ${clean.name || clean.email}`.slice(0, 200),
      html: `<h2>New ${esc(label)} submission</h2><table>${rows}</table>`,
      text,
    }),
  });
  if (!r.ok) { console.log("resend error", r.status, await r.text()); return json({ ok: false, error: "Send failed" }, 502); }
  const { id } = await r.json();
  if (confirm) {
    // Customer confirmation (approved by Matt 2026-10-17). A failure here never fails the submission.
    try {
      const c = confirm(clean);
      const cr = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({ from: "Obra Insights <forms@obrainsights.com>", to: [clean.email], reply_to: TO, subject: c.subject, html: c.html, text: c.text }),
      });
      if (!cr.ok) console.log("confirm error", cr.status, await cr.text());
    } catch (e) { console.log("confirm exception", String(e)); }
  }
  return json({ ok: true, id });
}
