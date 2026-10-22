import { handle } from "./_send.js";
import { brandedEmail } from "./_email.js";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
const MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace";
// Wording approved by Matt 2026-10-17. Keep it exact.
const confirm = (d) => ({
  subject: "We got your free app scan request",
  text: `Thanks for sending your app to Obra Insights. We'll review ${d.app_url} and email your scan report within 48 hours. If you have anything to add, just reply to this email.\n\nThe Obra Insights team\n\n--\nObra Insights | Human-led AI implementation for the real world\nhttps://obrainsights.com | info@obrainsights.com`,
  html: brandedEmail({
    title: "We got your free app scan request",
    preheader: "We'll email your scan report within 48 hours.",
    content:
      `<p style="margin:0;padding:0 0 8px 0;font-family:${MONO};font-size:11px;line-height:16px;letter-spacing:1.6px;text-transform:uppercase;font-weight:700;color:#c0401f;">Free app scan</p>` +
      `<h1 class="oi-h1" style="margin:0 0 18px 0;font-family:${SANS};font-size:26px;line-height:32px;font-weight:800;letter-spacing:-0.5px;color:#141110;">We got your request</h1>` +
      `<p style="margin:0 0 18px 0;font-family:${SANS};font-size:15px;line-height:24px;color:#141110;">Thanks for sending your app to Obra Insights. We'll review <b style="overflow-wrap:anywhere;word-break:break-word;">${esc(d.app_url)}</b> and email your scan report within 48 hours. If you have anything to add, just reply to this email.</p>` +
      `<p style="margin:0;font-family:${SANS};font-size:15px;line-height:24px;color:#141110;"><strong>The Obra Insights team</strong></p>`,
  }),
});
// Each request is stored in KV (binding SCAN_REQUESTS, production only) so scans/auto_scan.py can build and
// email the report automatically. Key: req:<ISO time>:<uuid>. The box script updates `status` once processed.
const store = async (d, env, request, alert_id) => {
  if (!env.SCAN_REQUESTS) return;
  const created_at = new Date().toISOString();
  const id = crypto.randomUUID();
  const rec = { id, created_at, status: "pending", alert_id, email: d.email, app_url: d.app_url, repo_url: d.repo_url,
    built_with: d.built_with, problem: d.problem, country: (request.cf && request.cf.country) || null,
    user_agent: (request.headers.get("user-agent") || "").slice(0, 300) };
  await env.SCAN_REQUESTS.put(`req:${created_at}:${id}`, JSON.stringify(rec));
};
export const onRequestPost = ({ request, env }) =>
  handle(request, env, { label: "Free Scan", fields: ["email", "app_url", "repo_url", "built_with", "problem"], required: ["email", "app_url", "problem"], confirm, store });
