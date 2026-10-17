import { handle } from "./_send.js";
export const onRequestPost = ({ request, env }) =>
  handle(request, env, { label: "Free Scan", fields: ["email", "app_url", "repo_url", "built_with", "problem"], required: ["email", "app_url", "problem"] });
