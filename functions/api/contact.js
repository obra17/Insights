import { handle } from "./_send.js";
export const onRequestPost = ({ request, env }) =>
  handle(request, env, { label: "Contact", fields: ["name", "email", "service", "link", "message"], required: ["name", "email", "message"] });
