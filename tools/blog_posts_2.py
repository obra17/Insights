"""Second batch of blog posts (Oct 17, 2026). Bodies are trusted HTML written in-repo."""

POSTS2 = [
{
"slug": "supabase-rls-auth-mistakes",
"title": "Supabase RLS and Auth Mistakes in AI-Built Apps (and How to Fix Them)",
"seo": "Supabase RLS and Auth Mistakes in AI-Built Apps",
"h1": 'Supabase RLS mistakes <span class="accent">your AI assistant made.</span>',
"desc": "Lovable, Bolt, and Cursor apps on Supabase often ship with open tables. Eight common RLS and auth mistakes, the Oct 30 grants change, and how to fix each.",
"date": "2026-10-17",
"read": "8 min read",
"body": """
<p>Supabase is the default backend for a huge share of vibe-coded apps. It's a great choice, but it comes with one rule that AI assistants routinely get wrong: <b>your anon key is public, so Row Level Security is the only thing standing between strangers and your data.</b></p>
<p>Anyone who opens your site can find the project URL and anon key in the JavaScript bundle. That's by design. It's only safe if every table has RLS turned on with the right policies. Here are the mistakes we see most often in AI-built apps, and how to fix them.</p>

<h2>1. RLS is turned off on a table</h2>
<p>Tables created through the SQL editor or a migration don't get RLS automatically, and assistants often generate <code>create table</code> statements without enabling it. Open the Supabase dashboard, go to Advisors, then Security Advisor, and look for "RLS disabled in public." Fix each table:</p>
<pre><code>alter table public.projects enable row level security;</code></pre>
<p>Enabling RLS with no policies blocks all access through the API, so your app will "break" right away. That's expected. Add the policies below next.</p>

<h2>Heads up: new tables need explicit grants from October 30, 2026</h2>
<p>Supabase is changing a default. Starting <b>October 30, 2026</b>, new tables you create in the <code>public</code> schema on existing projects are no longer exposed to the Data API (the REST and GraphQL layer <code>supabase-js</code> uses) until you grant access. Projects created since late May 2026 already work this way. Existing tables keep their grants. A new table without a grant returns <code>42501 permission denied for table ...</code>, even with correct policies. (<a href="https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically" rel="noopener">Supabase changelog</a>)</p>
<p>The danger is the "fix" your assistant reaches for: turning off RLS or granting everything to <code>anon</code>. Instead, have every migration that creates a table do three things together: grant only the roles and operations the app uses, enable RLS, and add owner policies.</p>
<pre><code>grant select, insert, update, delete on public.projects to authenticated;
alter table public.projects enable row level security;
-- then the owner policies below</code></pre>
<p>Only grant to <code>anon</code> if logged-out visitors genuinely need that table.</p>

<h2>2. The "fix" was <code>using (true)</code></h2>
<p>When the app breaks after RLS is enabled, the quickest prompt answer is a policy like <code>using (true)</code>. That makes the table readable by everyone again. Write policies that tie each row to its owner instead:</p>
<pre><code>create policy "Owners read their projects" on public.projects
  for select to authenticated
  using ((select auth.uid()) = user_id);

create policy "Owners insert their projects" on public.projects
  for insert to authenticated
  with check ((select auth.uid()) = user_id);</code></pre>
<p>Add matching <code>update</code> and <code>delete</code> policies. Wrapping <code>auth.uid()</code> in <code>select</code> lets Postgres evaluate it once per query instead of once per row, and an index on <code>user_id</code> keeps these queries fast as the table grows.</p>

<h2>3. Update policies without <code>with check</code></h2>
<p>An update policy with only <code>using</code> controls which rows a user can change, but not what they change them to. Without <code>with check</code>, a user can update their own row and set <code>user_id</code> to someone else's ID, or flip a <code>plan</code> column to "pro." Give update policies both clauses, and keep sensitive columns like plan, credits, and role out of tables users can write to.</p>

<h2>4. Roles stored where users can edit them</h2>
<p>A common AI-generated pattern is checking <code>user.user_metadata.role === "admin"</code>. User metadata can be changed by the signed-in user. Store roles in <code>app_metadata</code> (only server code with the service role can set it) or in a separate <code>user_roles</code> table that users can read but not write. Then check the role in your RLS policies or server code, not just by hiding buttons in the UI.</p>

<h2>5. The service_role key in the frontend</h2>
<p>The <code>service_role</code> key bypasses RLS entirely. If an assistant "fixed" a permissions error by swapping it in, every visitor now has admin access to your database. Search your built files and your repo for it. If you find it in client code, move that operation into a server function or Edge Function, then rotate the key in the dashboard. Deleting it from the code isn't enough; assume it has already been copied. Our guide to <a href="/blog/api-keys-leaking-ai-apps/">leaked API keys in AI-built apps</a> covers how to look.</p>

<h2>6. Views and functions that skip RLS</h2>
<p>Two quieter holes:</p>
<ul>
<li><b>Views</b> run with the permissions of whoever created them by default, which usually means RLS doesn't apply. On Postgres 15 and later, create views with <code>with (security_invoker = true)</code> so the caller's policies are enforced.</li>
<li><b>Functions marked <code>security definer</code></b> run as their owner and can be called through the API with <code>rpc()</code>. Only use them when you have to, check <code>auth.uid()</code> inside them, and set a fixed <code>search_path</code>.</li>
</ul>

<h2>7. Storage buckets left public</h2>
<p>Uploaded files live in Supabase Storage, which has its own policies on <code>storage.objects</code>. A public bucket means anyone with the URL can download the file. For invoices, ID photos, or anything private, use a private bucket, store files under a folder named after the user's ID, and add policies that check that folder against <code>auth.uid()</code>. Serve files with signed URLs that expire.</p>

<h2>8. Trusting the session on the server</h2>
<p>In server code (API routes, server components, middleware), <code>getSession()</code> reads whatever is in the cookie without re-verifying it. To decide whether a request is allowed, verify the user with <code>getUser()</code> (or verified JWT claims) before you trust the user ID. This matters most anywhere you use the service role key, because RLS won't catch the mistake for you.</p>

<h2>Two tests that take five minutes</h2>
<p><b>The anon test.</b> Copy your project URL and anon key from the browser, then request a table directly, as a logged-out stranger would:</p>
<pre><code>curl "https://YOUR-PROJECT.supabase.co/rest/v1/projects?select=*" \\
  -H "apikey: YOUR_ANON_KEY"</code></pre>
<p>You should get an empty list or an error, never real rows.</p>
<p><b>The two-user test.</b> Sign up as User A and create something. In a private window, sign up as User B and try to read or edit A's item, through the UI or by replaying A's request with B's token. If B can see A's data, fix that before you launch. More on this in <a href="/blog/fix-broken-vibe-coded-app/">how to fix a broken vibe-coded app</a>.</p>

<h2>Get a second opinion</h2>
<p>RLS problems are invisible until someone goes looking, and the people who go looking aren't always friendly. Our <a href="/scan/">free app scan</a> checks a public URL for exposed keys and obvious misconfigurations. The <a href="/rescue/">$99 Health Scan</a> reviews your policies table by table, and a <a href="/rescue/">$149 Quick Fix</a> covers a single issue like one leaky table, delivered as a pull request you approve.</p>
""",
},
{
"slug": "api-keys-leaking-ai-apps",
"title": "Leaked API Keys and Env Vars in Lovable, Bolt, and Cursor Apps: Find and Fix Them",
"seo": "Leaked API Keys in Lovable, Bolt and Cursor Apps",
"h1": 'Your API keys are probably <span class="accent">more public than you think.</span>',
"desc": "How API keys and env vars leak from AI-built apps, how to check your Lovable, Bolt, or Cursor project in ten minutes, and what to do if a key is exposed.",
"date": "2026-10-17",
"read": "7 min read",
"body": """
<p>AI coding tools are very good at making things work. They are less careful about <em>where</em> secrets end up. A common pattern: the app calls OpenAI or Stripe straight from the browser, the key sits in a <code>VITE_</code> variable, and the first person to open DevTools can copy it. The bill arrives a few days later.</p>
<p>Here's how keys leak from vibe-coded apps, how to check yours in about ten minutes, and what to do if you find one.</p>

<h2>Public keys vs. secret keys</h2>
<p>Not every key in your frontend is a problem. Some are meant to be public:</p>
<ul>
<li><b>Fine in the browser:</b> the Supabase anon (or publishable) key, the Stripe publishable key (<code>pk_live_</code>/<code>pk_test_</code>), Firebase web config, and analytics IDs. These are only safe if your database rules are right; see our <a href="/blog/supabase-rls-auth-mistakes/">Supabase RLS guide</a>.</li>
<li><b>Never in the browser:</b> Stripe secret keys (<code>sk_live_</code>, <code>rk_live_</code>), the Supabase <code>service_role</code> key, OpenAI or Anthropic keys (<code>sk-</code>, <code>sk-proj-</code>, <code>sk-ant-</code>), AWS keys (<code>AKIA</code>...), email API keys like Resend (<code>re_</code>) or SendGrid (<code>SG.</code>), and webhook signing secrets (<code>whsec_</code>).</li>
</ul>

<h2>How keys leak</h2>
<h3>1. The public prefix</h3>
<p>Vite apps (most Lovable and Bolt projects) expose any variable starting with <code>VITE_</code> to the browser. Next.js does the same for <code>NEXT_PUBLIC_</code>. When an assistant hits "undefined" for a secret, the fastest fix is adding that prefix. It works, and it publishes the secret in your JavaScript bundle.</p>
<h3>2. The committed <code>.env</code> file</h3>
<p>If <code>.env</code> isn't in <code>.gitignore</code> before your first commit, it goes to GitHub with everything else. Making the repo private later doesn't help if it was ever public, and deleting the file doesn't remove it from git history.</p>
<h3>3. Hard-coded keys</h3>
<p>Sometimes the key is pasted right into a component, like <code>const openai = new OpenAI({ apiKey: "sk-..." })</code>, often because you pasted it into the chat and the assistant used it directly.</p>
<h3>4. Logs, errors, and screenshots</h3>
<p>Keys also show up in <code>console.log</code> output, error messages returned to the browser, demo videos, livestreams, and screenshots shared on X when asking for help.</p>

<h2>Check your app in ten minutes</h2>
<ol>
<li><b>Search the live site.</b> Open your deployed app, open DevTools, go to Sources (Chrome) or Debugger (Firefox), and search all files (Ctrl/Cmd+Shift+F) for <code>sk_live</code>, <code>sk-</code>, <code>service_role</code>, <code>AKIA</code>, <code>re_</code>, and <code>whsec_</code>.</li>
<li><b>Search the build.</b> Run <code>npm run build</code>, then search the output folder: <code>grep -rE "sk_live|sk-|service_role|AKIA|whsec_" dist/</code> (or <code>.next/</code>). To catch a <code>service_role</code> key, decode any JWT you find and check its <code>role</code> claim.</li>
<li><b>Search the repo, including history.</b> <code>git log -p | grep -E "sk_live|sk-|service_role"</code> is a quick check. Tools like gitleaks or trufflehog do a thorough one. On GitHub, turn on secret scanning and push protection for the repo.</li>
<li><b>Check every prefixed variable.</b> List every <code>VITE_</code> or <code>NEXT_PUBLIC_</code> variable in your <code>.env</code> and host settings. Each one should be something you'd be comfortable printing on your homepage.</li>
</ol>

<h2>If you find a leaked key</h2>
<ol>
<li><b>Rotate it first.</b> Create a new key in the provider's dashboard and revoke the old one. Removing it from your code doesn't help if it's already been copied, and bots scan GitHub for new keys within minutes.</li>
<li><b>Check usage.</b> Look at the provider's usage and billing pages for activity you don't recognize, and set spend limits or budget alerts where the provider offers them.</li>
<li><b>Move the call to the server.</b> Anything that needs a secret belongs in a server function: a Supabase Edge Function, a Vercel or Netlify function, or a Cloudflare Worker. The browser calls your function; your function holds the key and calls the provider.</li>
<li><b>Store the secret in the right place.</b> Put it in your host's environment settings or your Edge Function secrets, never in a prefixed variable and never in the repo.</li>
<li><b>Restrict what's left.</b> Use restricted Stripe keys with only the permissions you need, and lock Google API keys to your domain.</li>
</ol>

<h2>Keep it from happening again</h2>
<ul>
<li>Add <code>.env*</code> to <code>.gitignore</code> on day one and commit a <code>.env.example</code> with blank values instead.</li>
<li>Tell your assistant up front: "Never put secret keys in client code or in VITE_ or NEXT_PUBLIC_ variables. Use a server function." Put that line in your project rules file.</li>
<li>In Cursor, add <code>.env</code> to <code>.cursorignore</code> so it isn't sent to the AI as context.</li>
<li>Don't paste live keys into AI chats. Use placeholder values and add the real ones in your host's dashboard.</li>
</ul>

<h2>Want someone to check?</h2>
<p>Our <a href="/scan/">free app scan</a> looks at a public URL or public repo for exposed secrets and obvious config problems, and emails you what to fix first. If something turns up, a <a href="/rescue/">$149 Quick Fix</a> moves one leaky integration behind a server function, or the <a href="/rescue/">$99 Health Scan</a> audits the whole app. If your deploy is also failing, start with <a href="/blog/ai-app-wont-deploy/">our deploy checklist</a>.</p>
""",
},
{
"slug": "first-ai-agent-small-business",
"title": "How to Set Up Your First AI Agent for a Small Business (Without the Hype)",
"seo": "How to Set Up Your First AI Agent for a Small Business",
"h1": 'Your first AI agent: <span class="accent">one job, done well.</span>',
"desc": "A practical, step-by-step guide to setting up a first AI agent for a small business: picking the right job, permissions, testing, human approval, and running costs.",
"date": "2026-10-17",
"read": "8 min read",
"body": """
<p>Most small businesses don't need an "autonomous AI workforce." They need one tedious job taken off someone's plate, done reliably, without the agent emailing a customer something strange at 2 a.m. That's a very achievable goal. Here's how to get there.</p>

<h2>1. Pick one job, not a department</h2>
<p>The best first agent handles work that is:</p>
<ul>
<li><b>Repetitive:</b> it happens daily or weekly, in roughly the same shape.</li>
<li><b>Text-heavy:</b> reading, sorting, summarizing, or drafting.</li>
<li><b>Low-risk if it's wrong:</b> a person reviews the output before it matters.</li>
<li><b>Easy to check:</b> you can tell in seconds whether the result is good.</li>
</ul>
<p>Good first jobs include triaging an inbox and drafting replies, researching leads and drafting first-touch messages, turning one video or podcast into posts and a newsletter, and summarizing support tickets into a weekly report. Bad first jobs include anything that moves money, signs contracts, or talks to customers without review.</p>

<h2>2. Write the job down like you'd train a new hire</h2>
<p>Before touching any tool, write a one-page brief:</p>
<ul>
<li><b>Trigger:</b> what starts the work (a new email, a new row in a sheet, 8 a.m. every weekday).</li>
<li><b>Inputs:</b> what the agent can see.</li>
<li><b>Steps:</b> how a good employee does it today, including the judgment calls.</li>
<li><b>Output:</b> exactly what "done" looks like, and where it goes (a draft, a label, a row, a Slack message to you).</li>
<li><b>Never:</b> the things it must not do.</li>
</ul>
<p>If you can't write this page, the agent won't be able to follow it either. This document becomes the agent's instructions.</p>

<h2>3. Choose the simplest tool that works</h2>
<p>You don't need to write code for a first agent. Roughly in order of effort:</p>
<ul>
<li><b>Built-in assistants</b> in tools you already use (your email, CRM, or helpdesk) for simple summarize-and-draft jobs.</li>
<li><b>Automation platforms</b> like Zapier, Make, or n8n, which connect a trigger, an AI step, and an action with no code.</li>
<li><b>Agent frameworks or custom code</b> when the job needs several tools, memory, or branching logic.</li>
</ul>
<p>Whatever you choose, run it on <b>accounts your business owns</b>, with the model API billed to you. You want to keep the agent if you part ways with whoever built it.</p>

<h2>4. Give it the least access it needs</h2>
<p>This is where most of the risk lives. Give the agent read access and the ability to create <em>drafts</em>, labels, or notes, not to send, delete, or pay. Use a dedicated account or API key for the agent so you can see what it did and revoke access in one click. Add the "send" permission later, one category at a time, once you trust it.</p>

<h2>5. Keep a human approval step</h2>
<p>For anything customer-facing, the agent drafts and a person approves. In practice that's a draft sitting in your email, a message in Slack with Approve and Edit buttons, or a row in a sheet waiting for a checkmark. It sounds slow, but reviewing a good draft takes seconds, and the time saved is still most of the job.</p>

<h2>6. Test with real examples before going live</h2>
<p>Collect 20 to 30 real past examples (emails, leads, transcripts) including a few awkward ones. Run the agent on all of them and grade each result: right, fixable, or wrong. Change the instructions and run them again until the "wrong" pile is basically empty. Keep this set. Every time you change a prompt, or the model provider updates its model, rerun it.</p>

<h2>7. Run it in shadow mode for a week</h2>
<p>Let the agent work on live inputs while you keep doing the job as usual, and compare. You'll find the cases your test set missed. When the agent matches your judgment most of the time and the misses are harmless, switch to approval mode for real.</p>

<h2>8. Watch cost, errors, and drift</h2>
<ul>
<li><b>Cost:</b> set a monthly spend limit on the model API. For a low-volume job, usage is often modest, but a loop or a flood of inputs can surprise you.</li>
<li><b>Errors:</b> make failures loud. A silent agent that stopped working a week ago is worse than no agent.</li>
<li><b>Drift:</b> models, APIs, and your business change. Review a sample of the agent's work every week or two, and keep a short runbook so someone else can fix it.</li>
</ul>

<h2>A realistic first month</h2>
<p>Week one: pick the job and write the brief. Week two: build it and test on past examples. Week three: shadow mode. Week four: approval mode, with a weekly review. By the end of the month you should know whether it saves real time, and which job to automate next.</p>

<h2>Want it done for you?</h2>
<p>Our <a href="/agents/">Agent Setup Concierge</a> builds single-job agents (Inbox Triage, Content Repurposing, and Lead Research) on accounts you own, with human approval for anything that sends a message or spends money, a runbook, and monitoring. A <a href="/agents/">Single Agent setup is $1,200</a> and includes a free first month of Care. See <a href="/pricing/">all pricing</a>.</p>
""",
},
]
