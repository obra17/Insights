import { handle } from "./_send.js";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const confirm = (d) => ({
  subject: "We got your free app scan request",
  text: `Thanks for sending your app to Obra Insights. We'll review ${d.app_url} and email your scan report within 48 hours. If you have anything to add, just reply to this email.\n\nThe Obra Insights team`,
  html: `<p>Thanks for sending your app to Obra Insights. We'll review <b>${esc(d.app_url)}</b> and email your scan report within 48 hours. If you have anything to add, just reply to this email.</p><p>The Obra Insights team</p>`,
});
export const onRequestPost = ({ request, env }) =>
  handle(request, env, { label: "Free Scan", fields: ["email", "app_url", "repo_url", "built_with", "problem"], required: ["email", "app_url", "problem"], confirm });
