"""Blog post content for obrainsights.com/blog/. Bodies are trusted HTML written in-repo."""

POSTS = [
{
"slug": "ai-app-wont-deploy",
"title": "Lovable, Bolt, or Cursor App Won't Deploy? 9 Fixes That Actually Work",
"h1": 'Your AI-built app won\'t deploy. <span class="accent">Here\'s what to check.</span>',
"desc": "Works in the preview, fails in production? The nine most common reasons Lovable, Bolt, Cursor, Replit, and v0 apps won't deploy, and how to fix each one.",
"date": "2026-10-16",
"read": "7 min read",
"body": """
<p>You built something in Lovable, Bolt, Cursor, Replit, or v0. It works in the preview. Then you hit deploy and get a build error, a blank white screen, or a site that loads but can't log anyone in.</p>
<p>The good news: the code is rarely the problem. Most failed deploys of vibe-coded apps come down to a handful of configuration issues the AI tool hid from you while you were inside its sandbox. Here are the nine we see most often, in the order you should check them.</p>

<h2>1. Read the actual build log first</h2>
<p>Before changing anything, open the build or deploy log on your host (Vercel, Netlify, Cloudflare Pages, Render, or the AI tool's own publish screen) and scroll to the <em>first</em> red line. Not the last one. The last error is usually a side effect. The first one tells you what broke.</p>
<p>Copy that line, and only that line, into your AI assistant along with the file it points to. Pasting the whole log invites the assistant to "fix" five unrelated things at once.</p>

<h2>2. Environment variables are missing in production</h2>
<p>This is the number one cause. Your <code>.env</code> file lives on your machine or inside the AI tool. Your host has never seen it. Add every variable in your host's dashboard (Settings, then Environment Variables) and redeploy.</p>
<p>Two details catch people out:</p>
<ul>
<li><b>Client-side prefixes.</b> Vite apps (most Lovable and Bolt exports) only expose variables that start with <code>VITE_</code>. Next.js apps need <code>NEXT_PUBLIC_</code>. Without the prefix, the value is <code>undefined</code> in the browser.</li>
<li><b>Build time, not run time.</b> Vite and Next.js bake public variables into the bundle when the app builds. If you add a variable after deploying, you must rebuild, not just restart.</li>
</ul>
<p>And never put a secret key (Stripe secret, Supabase <code>service_role</code>, OpenAI key) in a <code>VITE_</code> or <code>NEXT_PUBLIC_</code> variable. Anything with those prefixes is readable by anyone who opens your site.</p>

<h2>3. Blank white screen after deploy</h2>
<p>A white screen almost always means JavaScript crashed before it could render. Open the browser console (right-click, Inspect, Console). You'll typically see one of these:</p>
<ul>
<li><code>Failed to load module script</code> or 404s on <code>/assets/*.js</code>: your host is serving from the wrong folder. Set the output directory to <code>dist</code> (Vite) or leave the Next.js default.</li>
<li><code>supabaseUrl is required</code> or similar: a missing environment variable (see #2).</li>
<li>A wrong <code>base</code> path in <code>vite.config</code> if you deploy to a subfolder.</li>
</ul>

<h2>4. Refreshing any page gives a 404</h2>
<p>Single-page apps handle routing in the browser. When you refresh <code>/dashboard</code>, the host looks for a real file called <code>dashboard</code>, doesn't find one, and returns 404. Add a rewrite so every unknown path serves <code>index.html</code>:</p>
<ul>
<li><b>Netlify / Cloudflare Pages:</b> a <code>_redirects</code> file in your public folder containing <code>/* /index.html 200</code>.</li>
<li><b>Vercel:</b> a <code>rewrites</code> rule in <code>vercel.json</code> that sends <code>/(.*)</code> to <code>/index.html</code>.</li>
</ul>

<h2>5. Login works in preview but breaks in production</h2>
<p>If you use Supabase Auth, go to Authentication, then URL Configuration. Set the Site URL to your live domain and add <code>https://yourdomain.com/**</code> to the Redirect URLs. If you use Google or GitHub sign-in, add the live domain to that provider's OAuth client too. Localhost and the preview URL don't cover production. This is behind most "login loop" and "redirects back to localhost" reports.</p>

<h2>6. The build fails on type or lint errors</h2>
<p>Preview environments are often forgiving. Production builds aren't. <code>next build</code> runs a type check, and a single <code>any</code> mismatch the AI introduced three prompts ago can block the whole deploy. Run <code>npm run build</code> locally to see the same errors. Fix the types rather than switching off checking; the errors usually point at a real bug.</p>

<h2>7. Wrong Node version or a messy lockfile</h2>
<p>If the log mentions an unsupported engine, a syntax error inside <code>node_modules</code>, or <code>npm ci</code> failing, pin the Node version your app was built with (an <code>.nvmrc</code> file or the host's Node setting) and make sure exactly one lockfile is committed. Having both <code>package-lock.json</code> and <code>bun.lockb</code> or <code>pnpm-lock.yaml</code> confuses most hosts.</p>

<h2>8. File names that differ only by case</h2>
<p>macOS and Windows don't care whether you import <code>./components/Header</code> or <code>./components/header</code>. Linux build servers do. If the log says a module can't be found but you can see the file, check the capitalization.</p>

<h2>9. Payments and webhooks don't fire</h2>
<p>Stripe checkout opens, the customer pays, and nothing happens in your app. Check that the webhook endpoint is registered for the right mode (test and live are separate), that you're using that endpoint's own signing secret, and that your handler verifies the signature against the raw request body. Grant access from the verified webhook, never from the success-page URL, or anyone can unlock your product by visiting that page.</p>

<h2>When to stop prompting</h2>
<p>If your assistant has "fixed" the same deploy error three times and it's still failing, stop. Every extra prompt adds changes you'll have to untangle later. Revert to the last commit that built cleanly, then work through the checklist above one item at a time.</p>
<p>And if you'd rather have someone look at it with fresh eyes, that's exactly what we do.</p>
""",
},
{
"slug": "fix-broken-vibe-coded-app",
"title": "How to Fix a Broken Vibe-Coded App (Without Making It Worse)",
"h1": 'How to fix a broken vibe-coded app <span class="accent">without making it worse.</span>',
"desc": "Your AI assistant keeps breaking things while fixing them. A practical, step-by-step method for repairing Cursor, Lovable, Bolt, and Replit apps safely.",
"date": "2026-10-16",
"read": "7 min read",
"body": """
<p>Every vibe coder knows this loop. Something breaks. You ask the AI to fix it. It fixes that and breaks two other things. You ask again. An hour later the app is worse than when you started, and you're not sure which of the last twenty changes caused it.</p>
<p>The way out isn't a better prompt. It's a better process. Here's the one we use on rescue jobs, adapted so you can do it yourself.</p>

<h2>Step 1: Freeze and save a checkpoint</h2>
<p>Stop prompting. Commit everything as it is right now, broken or not, with a message like <code>checkpoint before fix</code>. If your project isn't in Git yet, connect it to GitHub today. Lovable, Bolt, and Replit can all sync to a repo.</p>
<p>One caution: if your tool syncs both ways with GitHub, decide which side is the source of truth before you edit anywhere else. Editing the repo by hand while the AI tool keeps its own copy is how people lose a week of work.</p>
<p>Then find the last version that worked. Most tools keep a version history; Git has <code>git log</code>. Knowing the last good point turns "everything is broken" into "something changed between Tuesday and today."</p>

<h2>Step 2: Write down exactly what's broken</h2>
<p>Vague problems get vague fixes. For each issue, write three lines:</p>
<ul>
<li><b>What I did:</b> "Logged in as a new user and clicked Save on the profile page."</li>
<li><b>What I expected:</b> "Profile saves and shows a success message."</li>
<li><b>What happened:</b> "Spinner forever. Console shows 403 on <code>/rest/v1/profiles</code>."</li>
</ul>
<p>That last line matters. Open the browser console and the network tab, reproduce the bug, and copy the first error. Ninety percent of the diagnosis is in that one message.</p>

<h2>Step 3: Rank the problems, then fix one at a time</h2>
<p>Sort your list by severity. Our order is: security issues first (anyone can read other users' data, keys exposed), then anything that blocks signup, login, or payment, then broken features, then cosmetic issues.</p>
<p>Then give the AI exactly one problem per conversation. A good fix prompt looks like this:</p>
<p><code>Bug: [the three lines from step 2]. Error: [the first console error]. Relevant file: [path]. Before changing code, list the 3 most likely root causes and tell me how to confirm each one. Change only what's needed for the confirmed cause.</code></p>
<p>Asking for causes before code stops the assistant from rewriting half your app on a guess.</p>

<h2>Step 4: The two-strike rule</h2>
<p>If a fix doesn't work, revert it before trying the next idea. If two fixes in a row fail, stop and add logging instead of more changes: print the values going in and out of the function that's failing. Stacking failed fixes on top of each other is the single biggest reason vibe-coded apps spiral.</p>

<h2>Step 5: Check the usual suspects</h2>
<p>Most broken AI-built apps we look at have at least one of these:</p>
<ul>
<li><b>Row Level Security off or too open.</b> In Supabase, every table that holds user data needs RLS enabled and policies that limit rows to their owner. A policy of <code>USING (true)</code> means anyone can read everything.</li>
<li><b>Roles checked in the browser.</b> Hiding the admin button isn't security. Check roles on the server or in the database policy, not in <code>user_metadata</code> the user can edit.</li>
<li><b>Secrets in the frontend.</b> Search your built JavaScript for <code>sk_live</code>, <code>service_role</code>, or <code>sk-</code>. If they're there, move those calls to a server function and rotate the keys.</li>
<li><b>Missing environment variables</b> in production (see our <a href="/blog/ai-app-wont-deploy/">deploy checklist</a>).</li>
<li><b>Webhooks that trust the success URL</b> instead of a verified Stripe event.</li>
</ul>

<h2>Step 6: The two-user test</h2>
<p>This takes sixty seconds and catches the most dangerous bug in vibe-coded apps. Sign up as User A and create something. Open a private window, sign up as User B, and try to view or edit User A's item, either through the UI or by replaying A's network request. If B can see A's data, fix that before anything else.</p>

<h2>Step 7: Verify, then lock it in</h2>
<p>After each fix, reproduce the original steps and confirm the bug is gone. Then click through signup, login, the main feature, and payment to make sure nothing else broke. Commit with a clear message (<code>fix: profile save 403, add owner RLS policy</code>). Small, labeled commits make the next bug much easier to find.</p>
<p>If you can, turn the bug into a quick test or a line in a checklist so the next "quick fix" from your assistant doesn't quietly reopen it.</p>

<h2>When it's time to get help</h2>
<p>Bring in a second pair of eyes if you've spent more than a day on the same bug, if the problem involves other people's data or money, or if every fix creates a new problem. Sometimes the honest answer is that a section needs rebuilding, and it's better to know that early.</p>
<p>Our Health Scan does the steps above for you: a severity-ranked report with evidence, and fixes delivered as pull requests you approve. Start with the free scan to see what turns up.</p>
""",
},
{
"slug": "launch-ai-app-from-prompt",
"title": "How to Launch an AI App From a Prompt: Idea to Live URL in a Weekend",
"h1": 'From prompt to <span class="accent">live URL in a weekend.</span>',
"desc": "A practical weekend plan for turning an idea into a launched AI-built app: scope, build, domain, auth, payments, analytics, and announcing it.",
"date": "2026-10-16",
"read": "8 min read",
"body": """
<p>AI tools have made building the first version of an app almost free. Launching it is a different story. Most vibe-coded projects stall in the gap between "it works on my screen" and "strangers are using it." This guide closes that gap with a plan you can finish in a weekend.</p>

<h2>Friday night: shrink the idea</h2>
<p>The fastest way to never launch is to start with ten features. Write one sentence: <em>"[Who] can [do one thing] so they [get one result]."</em> For example: "Wedding photographers can turn a client questionnaire into a shot list in one click."</p>
<p>Then list what's needed to deliver that sentence and nothing else. Usually that's a landing page, a sign-up, the one core action, and a way to pay or join a waitlist. Settings pages, dark mode, and team accounts can wait for version two.</p>

<h2>Friday night: pick your tool and stack</h2>
<p>Choose based on where you are, not what's trending:</p>
<ul>
<li><b>No code experience:</b> Lovable, Bolt, or v0 for the UI, with Supabase for login and data.</li>
<li><b>Some code experience:</b> Cursor or Claude Code on a standard stack (Next.js or Vite with Supabase) so you can take the code anywhere.</li>
<li><b>Just validating demand:</b> skip the app. A landing page and waitlist will tell you more in a week.</li>
</ul>
<p>Whatever you pick, connect a GitHub repo from day one. You want to own your code, not rent it from the tool.</p>

<h2>Saturday morning: write the prompt like a spec</h2>
<p>A good first prompt reads like a one-page brief: who the user is, the one core flow step by step, what data you store, and what the user sees when something goes wrong. Ask the tool to build the core flow first, with fake data, before adding login or payments.</p>
<p>Build in small steps and commit after each one that works. "Add the shot list page" is a good prompt. "Build the whole app" is how you end up with a codebase nobody understands.</p>

<h2>Saturday afternoon: add login and data safely</h2>
<p>Add authentication once the core flow works. If you're on Supabase, do two things right away:</p>
<ul>
<li>Turn on Row Level Security for every table and add policies so users can only read and write their own rows.</li>
<li>Run the two-user test: sign up as two different users and confirm neither can see the other's data.</li>
</ul>
<p>Keep secret keys on the server. Anything in a <code>VITE_</code> or <code>NEXT_PUBLIC_</code> variable is public.</p>

<h2>Saturday evening: deploy early</h2>
<p>Deploy the moment you have a working core flow, even if it's ugly. Deploying on Sunday night is when people discover missing environment variables, broken auth redirects, and 404s on refresh. Our <a href="/blog/ai-app-wont-deploy/">deploy troubleshooting guide</a> covers the usual problems.</p>
<p>Then connect your domain. Buy it from any registrar, point it at your host following the host's instructions, and make sure HTTPS works on both the bare domain and <code>www</code>. Update your auth provider's redirect URLs to the new domain.</p>

<h2>Sunday morning: payments or a waitlist</h2>
<p>If you're charging from day one, the simplest path is a hosted checkout: Stripe Payment Links or Stripe Checkout. You don't handle card details, and you can test everything in Stripe's test mode with test cards before going live. If your app unlocks features after payment, grant access from a verified webhook, not from the thank-you page.</p>
<p>Not ready to charge? Put up a waitlist with a clear promise ("Early access in November, founding price locked in") and collect emails with a newsletter tool.</p>

<h2>Sunday afternoon: the launch checklist</h2>
<p>Before you tell anyone, run through this list:</p>
<ul>
<li>Sign up, log in, log out, and reset a password on your phone and your laptop.</li>
<li>Complete the core action and a test payment end to end.</li>
<li>Check that your page titles, descriptions, and social preview image look right when you paste the link into a message.</li>
<li>Add basic analytics so you can see where people drop off.</li>
<li>Add a contact email and short Terms and Privacy pages.</li>
<li>Submit your sitemap to Google Search Console.</li>
</ul>

<h2>Sunday evening: announce it</h2>
<p>Write one short post that explains the problem, shows the product in a screenshot or 30-second clip, and gives one link. Share it where your users already are: X, a relevant subreddit, a Discord, or a Product Hunt launch later in the week. Reply to every comment. Your first ten users will tell you what version two should be.</p>

<h2>What usually goes wrong</h2>
<p>When launches slip, it's rarely the idea. It's the plumbing: DNS, auth redirects, environment variables, webhooks, or an AI assistant stuck in a loop on the last bug. If that's where you are, you're closer than it feels.</p>
<p>That last stretch is what we do. Our Prompt-to-Launch Kit gets a landing page, waitlist, and launch copy live on your domain in 72 hours, and our App Rescue fixes AI-built apps that won't make it to production. Not sure which you need? Start with the free scan.</p>
""",
},
]
