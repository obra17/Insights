#!/usr/bin/env python3
"""Generates the static site into public/. No dependencies. Run: python3 tools/build.py"""
import hashlib as _hl
import json, os, html, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SITE = "https://obrainsights.com"
OUT = os.environ.get("OBRA_OUT") or os.path.join(os.path.dirname(__file__), "..", "public")
_CSS_SRC = os.path.join(os.path.dirname(__file__), "..", "public", "assets", "style.css")
CSS_VER = _hl.md5(open(_CSS_SRC,"rb").read()).hexdigest()[:8] if os.path.exists(_CSS_SRC) else "1"
# Buy buttons (Stripe Payment Links) are OFF by default. Production builds never set SHOW_BUY.
# Preview only: SHOW_BUY=1 OBRA_OUT=/tmp/obra-preview python3 tools/build.py
# Live (after Stripe activation): SHOW_BUY=1 STRIPE_LIVE=1 python3 tools/build.py  -> uses tools/stripe_live_links.json,
# no test banner, normal indexing. Without STRIPE_LIVE, SHOW_BUY builds are test previews (banner + noindex).
SHOW_BUY = os.environ.get("SHOW_BUY") == "1"
STRIPE_LIVE = SHOW_BUY and os.environ.get("STRIPE_LIVE") == "1"
TEST_PREVIEW = SHOW_BUY and not STRIPE_LIVE
_links_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stripe_live_links.json" if STRIPE_LIVE else "stripe_test_links.json")
STRIPE_LINKS = {k:v for k,v in json.load(open(_links_file)).items() if not k.startswith("_")} if SHOW_BUY else {}
if STRIPE_LIVE: assert all("/test_" not in u for u in STRIPE_LINKS.values()), "live build with test links"
if TEST_PREVIEW and OUT == os.path.join(os.path.dirname(__file__), "..", "public"): sys.exit("refusing: test-checkout preview must use OBRA_OUT, not public/")
def buy(name, cls="btn"):
    u = STRIPE_LINKS.get(name)
    return f'<a class="{cls}" href="{e(u)}" rel="nofollow">Buy now</a>' if u else ""
# TODO(endpoints): set these to real form endpoints (e.g. Formspree, Tally, Netlify Forms, Cloudflare Worker).
# While empty, forms validate but show a "not connected yet" notice instead of pretending to submit.
SCAN_ENDPOINT = "/api/scan"        # Cloudflare Pages Function -> Resend -> info@
# Newsletter: Beehiiv embed on /newsletter/ (https://obrainsights.beehiiv.com)
CONTACT_ENDPOINT = "/api/contact"  # Cloudflare Pages Function -> Resend -> info@

NAV = [("/launch-kit/","Launch Kit"),("/rescue/","App Rescue"),("/agents/","Agent Setup"),("/pricing/","Pricing"),("/blog/","Blog"),("/about/","About")]
ORG = {"@type":"Organization","@id":SITE+"/#org","name":"Obrainsights","url":SITE+"/","logo":SITE+"/assets/brand/obra-mark.png","email":"info@obrainsights.com","contactPoint":{"@type":"ContactPoint","contactType":"customer support","email":"info@obrainsights.com"},
       "description":"Productized services that take an idea, prompt, or half-broken vibe-coded app to a live, working product, delivered by AI agents and verified by a human."}

def e(s): return html.escape(s, quote=True)

def faq_html(faqs):
    return '<section class="faq"><h2>FAQ</h2>' + "".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in faqs) + '</section>'
def faq_ld(faqs):
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]}
def service_ld(name, desc, path, offers):
    return {"@type":"Service","name":name,"description":desc,"url":SITE+path,"provider":{"@id":SITE+"/#org"},"areaServed":"Worldwide",
            "offers":[offer_ld(n,p) for n,p in offers]}
MONTHLY = {"Care","Ops","Pro"}
def offer_ld(n, p):
    o = {"@type":"Offer","name":n,"price":p,"priceCurrency":"USD"}
    if n in MONTHLY:
        o["priceSpecification"] = {"@type":"UnitPriceSpecification","price":p,"priceCurrency":"USD","unitText":"MONTH","billingDuration":"P1M"}
    return o

def tiers(rows):
    out = '<div class="tiers">'
    for name, price, inc, tat in rows:
        out += f'<div class="card tier"><h3>{e(name)}</h3><p class="price">{e(price)}</p><p>{e(inc)}</p><p class="muted">Turnaround: {e(tat)}</p>{buy(name)}<a class="btn ghost" href="/contact/">Request this tier</a></div>'
    note = "Pay securely with Stripe, or request a tier and we'll reply with a written scope first." if SHOW_BUY else "Checkout opens soon; until then, request a tier and we'll reply with a written scope."
    return out + f'</div><p class="muted small">Launch pricing (proposed). Fixed price, paid upfront. {e(note)}</p>'

def form(fid, endpoint, fields, button):
    f = "".join(fields)
    return f'''<form class="card form" id="{fid}" data-endpoint="{e(endpoint)}" method="post" novalidate>{f}
<button class="btn" type="submit">{e(button)}</button><p class="form-status" role="status" aria-live="polite"></p></form>'''
def inp(name, label, typ="text", req=True, ph=""):
    r = " required" if req else ""
    return f'<label>{e(label)}{"" if req else " <span class=muted>(optional)</span>"}<input name="{name}" type="{typ}" placeholder="{e(ph)}"{r}></label>'
def ta(name, label, req=False, ph=""):
    r = " required" if req else ""
    return f'<label>{e(label)}<textarea name="{name}" rows="4" placeholder="{e(ph)}"{r}></textarea></label>'
def sel(name, label, opts):
    return f'<label>{e(label)}<select name="{name}">' + "".join(f"<option>{e(o)}</option>" for o in opts) + '</select></label>'
HONEYPOT = '<input type="text" name="_gotcha" tabindex="-1" autocomplete="off" class="hp" aria-hidden="true">'

def page(path, title, desc, body, ld=None, pre="", og_type="website", noindex=False):
    url = SITE + path
    graph = [ORG] + (ld or [])
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h==path or (h=="/blog/" and path.startswith("/blog/")) else ""}>{t}</a>' for h,t in NAV)
    doc = f'''<!doctype html>
{pre}<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">{"" if path.endswith(".html") else f'<link rel="canonical" href="{url}">'}
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Obrainsights"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/assets/og.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{SITE}/assets/og.png">
{'<meta name="robots" content="noindex,nofollow">' if (TEST_PREVIEW or noindex) else ''}<meta name="theme-color" content="#f9f6f0"><link rel="icon" href="/favicon.ico?v=oi" sizes="48x48"><link rel="icon" href="/assets/brand/obra-oi.svg" type="image/svg+xml"><link rel="icon" href="/assets/brand/oi-favicon-192.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/assets/brand/oi-apple-touch-icon.png"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Playfair+Display:ital,wght@1,500;1,700&display=swap"><link rel="stylesheet" href="/assets/style.css?v={CSS_VER}">
<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@graph":graph})}</script>
</head><body>
<header class="top"><div class="wrap nav"><a class="brand" href="/"><img class="mark" src="/assets/brand/obra-mark-160.png" alt="Obra logo" width="40" height="40"><span class="wm">OBRA INSIGHTS<span class="dot">.</span></span></a><nav>{nav}<a class="btn sm" href="/scan/">Free App Scan</a></nav></div></header>
<main class="wrap">{'<p class="offer"><b>Preview with Stripe TEST checkout.</b> Buy buttons use Stripe test mode. Use card 4242 4242 4242 4242; no real charges.</p>' if TEST_PREVIEW else ''}{body}</main>
<footer class="foot"><div class="wrap cols">
<div><p class="brand foot-brand"><img class="oi" src="/assets/brand/obra-oi-96.png" srcset="/assets/brand/obra-oi-96.png 2x, /assets/brand/obra-oi-144.png 3x" alt="Obra Insights OI logo" width="48" height="48" loading="lazy" decoding="async"><span class="wm">OBRA INSIGHTS<span class="dot">.</span></span></p><p class="muted">From prompt to live, working product. Agent-delivered, human-verified.</p></div>
<div><p><b>Services</b></p><a href="/launch-kit/">Prompt-to-Launch Kit</a><a href="/rescue/">Vibe-Coded App Rescue</a><a href="/agents/">Agent Setup Concierge</a><a href="/pricing/">Pricing</a></div>
<div><p><b>Company</b></p><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/blog/">Blog</a><a href="/newsletter/">Newsletter</a><a href="/scan/">Free App Scan</a><a href="/llms.txt">llms.txt</a><a href="mailto:info@obrainsights.com">info@obrainsights.com</a></div>
<div><p><b>Legal</b></p><a href="/terms/">Terms of Service</a><a href="/privacy/">Privacy Policy</a></div>
</div><p class="wrap muted small">© 2026 Obrainsights. All prices in USD.</p></footer>
<script src="/assets/forms.js" defer></script></body></html>'''
    if path.endswith(".html"):
        fn = os.path.join(OUT, path.strip("/"))
    else:
        d = os.path.join(OUT, path.strip("/")); os.makedirs(d, exist_ok=True); fn = os.path.join(d, "index.html")
    open(fn, "w").write(doc)

LK_FAQ = [("What is the Prompt-to-Launch Kit?","A fixed-price package that turns your idea into a live one-page landing site on your own domain, with a waitlist or email capture, analytics, basic branding, and launch copy."),
 ("How long does it take?","72 hours for Starter, 4 business days for Standard, and 5 business days for Plus, counted from when your intake form is complete."),
 ("Do I own the site and domain?","Yes. You own the domain, the accounts, and the code. The repo or project is handed over at delivery."),
 ("What is not included?","Multi-page sites, custom backends, payments beyond a hosted checkout link, and paid ads.")]
RS_FAQ = [("What is Vibe-Coded App Rescue?","An audit-and-fix service for apps built with AI tools like Cursor, Lovable, Bolt, Replit, v0, or Claude Code. It covers deploy and hosting, auth and roles, security, bugs, and performance."),
 ("What is the $149 Quick Fix?","One specific bug or deploy issue, fixed and delivered as a pull request within 48 hours. Good when you already know what is broken. If the issue turns out to be bigger than one fix, we tell you before any work starts and quote a Fix Sprint instead."),
 ("What does the $99 Health Scan include?","An automated and agent-reviewed audit with a severity-ranked report and evidence, delivered in 48 hours. The $99 is credited toward a Quick Fix, Fix Sprint, or Launch-Ready tier."),
 ("How are fixes delivered?","As pull requests to your repository, with a plain-English handover note. You approve and merge; nothing is merged to production without your approval."),
 ("Do you need my production credentials?","Access is read-only by default and least-privilege. Credentials are never stored in chat or the repo, and access is revoked at handover."),
 ("What if my app needs a full rebuild?","Full rebuilds and migrations are out of scope. The Scan says when a rebuild makes more sense, and those jobs are quoted separately or referred out.")]
AG_FAQ = [("What agents do you set up?","The starting catalog is Inbox Triage, Content Repurposing, and Lead Research. Each agent is built for one job."),
 ("Whose accounts does the agent run on?","Yours. Agents run on accounts you own, and you pay model and API usage directly."),
 ("Can an agent send messages or spend money for me?","Only with a human-approval step that you control."),
 ("What does the retainer cover?","Monitoring, fixes when models or APIs change, prompt and eval tuning, and a set number of improvements each month, depending on tier. Retainers are month-to-month.")]
GEN_FAQ = [("What is Obrainsights?","A productized services business for solo builders that turns an idea, a prompt, or a half-broken vibe-coded app into a live, working product, then sets up AI agents to help run it."),
 ("Who does the work?","AI agents handle intake, scoping, delivery, QA, and follow-up. A human on our team approves pricing exceptions, credentials, payments, and final sign-off."),
 ("Are prices fixed?","Yes. Every tier has a fixed price and written scope, paid upfront. Work beyond a tier gets a fixed-price change order, never hourly billing."),
 ("Who owns the code and accounts?","You do. Customers own all accounts, domains, and code.")]

LK_T = [("Starter","$299","Landing page, waitlist, domain/DNS help, analytics, 1 revision","72 hours"),
        ("Standard","$599","Starter plus branding basics and a launch copy pack, 2 revisions","4 business days"),
        ("Plus","$999","Standard plus a Product Hunt kit, OG/social assets, and a demo video script","5 business days")]
RS_T = [("Health Scan","$99","Automated + agent-reviewed audit, severity-ranked report. Credited toward a fix.","48 hours"),
        ("Quick Fix","$149","One specific bug or deploy issue fixed, delivered as a PR with a short handover note","48 hours"),
        ("Fix Sprint","$750","Up to 5 critical/high issues fixed, PRs + handover, 7-day support","5 business days"),
        ("Launch-Ready","$1,950","Up to 12 issues + production deploy, auth/payments verified, 14-day support","10 business days")]
AG_T = [("Single Agent","$1,200 setup","One agent from the catalog, runbook, monitoring","5–7 business days"),
        ("Agent Pack","$2,900 setup","Three agents, shared dashboard","10 business days")]
RT_T = [("Care","$249/mo per agent","Monitoring, break-fix, monthly health report","Ongoing"),
        ("Ops","$599/mo (up to 3 agents)","Care + 1 improvement/month + 48-hour response","Ongoing"),
        ("Pro","$1,200/mo (up to 6 agents)","Ops + 3 improvements/month + priority response","Ongoing")]

def num(p): return p.replace("$","").replace(",","").split()[0].split("/")[0]

FOUNDING = "Founding customer offer: 30% off for our first 10 clients in exchange for a testimonial."
def founding_html():
    return f'<aside class="offer" aria-label="Founding customer offer"><p><b>{e(FOUNDING)}</b></p><p class="muted small">Applies to any package. Use code <b>FOUNDING30</b> at checkout for 30% off (first 10 customers; on retainers it covers the first month), or mention it when you request a written quote. In return, we ask for a short testimonial after delivery. Available while spots last.</p></aside>'

HOW = '''<section><h2>How it works</h2><ol class="steps">
<li><b>Tell us what you have.</b> An idea, a prompt, or a repo. Fill in a short intake form.</li>
<li><b>Get a fixed scope and price.</b> Written before you pay. No hourly billing.</li>
<li><b>Agents build, a human verifies.</b> AI agents do the delivery work; credentials, payments, and final sign-off go through a human checkpoint.</li>
<li><b>You own everything.</b> Code, domain, and accounts stay yours. Changes arrive as pull requests.</li></ol></section>'''

# Payment confirmation. Stripe Payment Links redirect to /thanks/?paid=<slug>.
PRODUCTS = {"lk-starter":"Prompt-to-Launch Kit: Starter","lk-standard":"Prompt-to-Launch Kit: Standard","lk-plus":"Prompt-to-Launch Kit: Plus",
 "rs-scan":"App Rescue: $99 Health Scan","rs-quickfix":"App Rescue: $149 Quick Fix","rs-sprint":"App Rescue: Fix Sprint","rs-launchready":"App Rescue: Launch-Ready",
 "ag-single":"Agent Setup: Single Agent","ag-pack":"Agent Setup: Agent Pack (3 agents)","rt-care":"Care retainer","rt-ops":"Ops retainer","rt-pro":"Pro retainer"}
PAID_FALLBACK = '''<div id="paid-fallback" class="offer" hidden><p><b>Payment received. Thank you!</b> <a id="paid-link" href="/thanks/">See your next steps</a>.</p></div>
<script>(function(){var q=new URLSearchParams(location.search),s=q.get("paid");if(!s)return;var u="/thanks/?paid="+encodeURIComponent(s);
var b=document.getElementById("paid-fallback");b.hidden=false;document.getElementById("paid-link").href=u;location.replace(u);})();</script>'''

# Home
page("/", "Obrainsights: From Prompt to Live, Working Product",
 "Fixed-price launch kits, vibe-coded app rescue, and done-for-you AI agents for solo builders. Agent-delivered, human-verified.",
 f'''<section class="hero home"><p class="eyebrow">Human-led AI implementation for the real world</p>
<h1>From prompt to <span class="accent">live, working product.</span></h1>
<p class="lead">At Obra Insights, we help businesses use AI as a practical tool to save time, cut wasted effort, and get real results, from a working app to AI agents that handle the busywork.</p>
<div class="cta"><a class="btn" href="/scan/">Get a free app scan</a><a class="btn ghost" href="/pricing/">See pricing</a></div></section>
{founding_html()}
<section><h2>Three services, one path</h2><div class="grid3">
<a class="card svc" href="/launch-kit/"><span class="tag">From $299</span><h3>Prompt-to-Launch Kit</h3><p>A live landing page on your domain with a waitlist, analytics, branding basics, and launch copy. 72 hours to 5 business days.</p></a>
<a class="card svc" href="/rescue/"><span class="tag">Scan $99</span><h3>Vibe-Coded App Rescue</h3><p>Your Cursor, Lovable, Bolt, or Replit app works in the demo but not in production. We audit it and fix it with pull requests.</p></a>
<a class="card svc" href="/agents/"><span class="tag">From $1,200</span><h3>Agent Setup Concierge</h3><p>Done-for-you AI agents for one job each: inbox triage, content repurposing, or lead research. Optional monthly care.</p></a>
</div></section>
<section><h2>Common problems we fix</h2><ul class="checks">
<li>Auth loops and broken role checks</li><li>Exposed API keys and missing Supabase RLS or Firebase rules</li><li>Deploys that fail outside the AI tool</li><li>Stripe webhooks that never fire</li><li>An AI assistant stuck fixing the same bug</li><li>No time to set up domain, DNS, and a waitlist</li></ul></section>
{HOW}
{faq_html(GEN_FAQ)}
<section class="band card"><h2>Not sure where to start?</h2><p>Run the free app scan. You'll get a short report by email with what to fix first.</p><a class="btn" href="/scan/">Start the free scan</a></section>''',
 [faq_ld(GEN_FAQ)])

def svc_page(path, title, desc, h1, lead, scope, deliver, out, tiersrows, faqs, sname, cta):
    extra = f'<section><h2>Retainers</h2>{tiers(RT_T)}</section>' if path=="/agents/" else ""
    page(path, title, desc, f'''<section class="hero sm"><p class="eyebrow">{e(sname)}</p><h1>{h1}</h1><p class="lead">{e(lead)}</p><div class="cta">{cta}</div></section>
<section class="grid2"><div class="card"><h2>Scope</h2><p>{e(scope)}</p></div><div class="card"><h2>Deliverables</h2><p>{e(deliver)}</p></div></section>
<section><h2>Tiers</h2>{tiers(tiersrows)}</section>{extra}
<section><h2>Out of scope</h2><p>{e(out)}</p></section>{faq_html(faqs)}''',
    [service_ld(sname, desc, path, [(n, num(p)) for n,p,_,_ in tiersrows] + ([(n, num(p)) for n,p,_,_ in RT_T] if path=="/agents/" else [])), faq_ld(faqs)])

svc_page("/launch-kit/","Launch Kit: Landing Page + Waitlist in 72 Hours | Obrainsights",
 "Fixed-price launch kit for solo builders: landing page on your domain, waitlist, analytics, branding, and launch copy. $299–$999.",
 'Your idea, <span class="accent">live in 72 hours.</span>',
 "A one-page landing site on your domain with everything you need to start collecting signups and announce your launch.",
 "One-page landing site, help connecting your domain and DNS (you own the domain), a waitlist or email capture, basic branding (wordmark, colors, fonts, favicon, social card), and launch copy (headline, one X thread, a Reddit/Discord post, a Product Hunt tagline).",
 "A live URL on your domain, the repo or project handed over, analytics connected, a launch copy doc, and a one-page brand sheet.",
 "Multi-page sites, custom backends, payments beyond a hosted checkout link, and paid ads.", LK_T, LK_FAQ, "Prompt-to-Launch Kit",
 '<a class="btn" href="/contact/">Start a Launch Kit</a><a class="btn ghost" href="/pricing/">Compare tiers</a>')
svc_page("/rescue/","Vibe-Coded App Rescue: Fix AI-Built Apps | Obrainsights",
 "Audit and fix apps built with Cursor, Lovable, Bolt, Replit, v0, or Claude Code. $99 Health Scan, $149 Quick Fix, $750 Fix Sprint, $1,950 Launch-Ready.",
 'The demo works. <span class="accent">Production doesn\'t.</span> Let\'s fix that.',
 "We audit and fix AI-built apps across deploy, auth, security, bugs, and performance, and deliver every fix as a pull request you approve.",
 "Audit and fix AI-built apps in five areas: deploy/hosting, auth and roles, security (secrets, Supabase RLS/Firebase rules, input validation), bugs, and performance.",
 "A scored Health Scan report (problems ranked by severity, with evidence), fixes delivered as pull requests to your repo, a plain-English handover note, and a short support window after delivery.",
 "Full rebuilds and migrations. The Scan says when an app should be rebuilt; those jobs are quoted separately or referred out.", RS_T, RS_FAQ, "Vibe-Coded App Rescue",
 '<a class="btn" href="/scan/">Try the free scan</a><a class="btn ghost" href="/contact/">Book a $99 Health Scan</a>')
svc_page("/agents/","Agent Setup Concierge: Done-for-You AI Agents | Obrainsights",
 "Done-for-you AI agents for inbox triage, content repurposing, and lead research, running on your accounts. Setup from $1,200, care from $249/mo.",
 'AI agents that <span class="accent">actually do the job.</span>',
 "We build single-job AI agents on accounts you own, document them, and keep them working when models and APIs change.",
 "Done-for-you AI agents, each built for one job. Inbox Triage labels mail, drafts replies, and sends a daily digest. Content Repurposing turns a video or stream into clips, X threads, a newsletter, and Shorts captions. Lead Research builds and enriches prospect lists and drafts first-touch messages for you to approve.",
 "A configured agent running on accounts you own, a runbook, a 30-minute async Loom walkthrough, and monitoring and alerting.",
 "Model and API usage fees (you pay those directly), and any agent action that sends messages or spends money without a human-approval step.", AG_T, AG_FAQ, "Agent Setup Concierge",
 '<a class="btn" href="/contact/">Pick an agent</a><a class="btn ghost" href="/pricing/">See retainers</a>')

PR_FAQ = [("Why is pricing marked proposed?","These are launch prices, set at the low end of published comparable rates. They may change after the first customers; any price you are quoted in writing is the price you pay."),
 ("How do I pay?","Fixed price, paid upfront via Stripe Checkout once your written scope is agreed."),
 ("Are there any discounts?","The $99 Scan fee is credited toward any Fix tier, including the $149 Quick Fix. Launch Kit buyers get $100 off an App Rescue within 60 days. Agent setups include one free month of Care. Our first 10 clients also get 30% off any package in exchange for a short testimonial; use code FOUNDING30 at checkout (30% off, first 10 customers) or mention it on your written quote."),
 ("What if I need more than my tier includes?","You get a fixed-price change order before any extra work starts. There is no hourly billing.")]
def table(title, rows):
    return f'<h2>{title}</h2><div class="tbl"><table><thead><tr><th>Tier</th><th>Price</th><th>Includes</th><th>Turnaround</th></tr></thead><tbody>' + "".join(f"<tr><td>{e(a)}</td><td><b>{e(b)}</b>{(' ' + buy(a, 'btn sm')) if SHOW_BUY else ''}</td><td>{e(c)}</td><td>{e(d)}</td></tr>" for a,b,c,d in rows) + "</tbody></table></div>"
page("/pricing/","Pricing: Launch Kits, App Rescue, AI Agents | Obrainsights",
 "All Obrainsights tiers in one place: Launch Kit $299–$999, App Rescue from $99, Agent setup from $1,200, retainers from $249/mo.",
 f'''<section class="hero sm"><p class="eyebrow">Launch pricing (proposed)</p><h1>Fixed prices. <span class="accent">No hourly billing.</span></h1><p class="lead">Every tier has a written scope before you pay. All prices in USD.</p></section>
{founding_html()}
<section>{table('<a href="/launch-kit/">Prompt-to-Launch Kit</a>', LK_T)}{table('<a href="/rescue/">Vibe-Coded App Rescue</a>', RS_T)}{table('<a href="/agents/">Agent Setup Concierge</a>', AG_T)}{table('Agent retainers (month-to-month)', RT_T)}</section>
<section class="card"><h2>Pricing rules</h2><ul class="checks"><li>Fixed price, paid upfront through Stripe.</li><li>The $99 Scan fee is credited toward any Fix tier, including the $149 Quick Fix.</li><li>Launch Kit buyers get $100 off a Rescue within 60 days.</li><li>Agent setups include one free month of Care.</li><li>Founding customers: 30% off any package for our first 10 clients, in exchange for a short testimonial. Use code FOUNDING30 at checkout or mention it on your quote.</li><li>Work beyond a tier gets a fixed-price change order.</li></ul></section>
{faq_html(PR_FAQ)}''', [faq_ld(PR_FAQ)])

SC_FAQ = [("What does the free scan check?","A limited set of checks on a public URL or public repository, such as exposed secrets, basic security headers, and obvious deploy or config problems. The paid $99 Health Scan goes much deeper."),
 ("How do I get the results?","By email. Free scans are reviewed before the report is sent."),
 ("Do you need access to my code?","No. Submit a public URL or public repo only. Never paste passwords, API keys, or private credentials into this form.")]
page("/scan/","Free App Scan for Vibe-Coded Apps | Obrainsights",
 "Submit your app URL or public repo for a free mini security and health scan. Get a short report by email with what to fix first.",
 f'''<section class="hero sm"><p class="eyebrow">Free tool</p><h1>Free <span class="accent">app scan</span></h1><p class="lead">Built with Cursor, Lovable, Bolt, Replit, v0, or Claude Code? Send us a public URL or repo and get a short report by email.</p></section>
<section class="grid2"><div>{form("scan-form", SCAN_ENDPOINT, [HONEYPOT, inp("email","Email","email",ph="you@example.com"), inp("app_url","App URL","url",ph="https://yourapp.com"), inp("repo_url","Public repo URL","url",False,"https://github.com/you/app"), sel("built_with","Built with",["Cursor","Lovable","Bolt","Replit","v0","Claude Code","Other / mixed"]), ta("problem","What's going wrong?",ph="e.g. login loops after deploy"), '<p class="muted small">Never include passwords, API keys, or private credentials.</p>'], "Request my free scan")}</div>
<div class="card"><h2>What happens next</h2><ol class="steps"><li>We run a limited automated scan on what you submit.</li><li>The results are reviewed before anything is sent.</li><li>You get a short report by email with issues ranked by severity.</li><li>If you want fixes, the <a href="/rescue/">$99 Health Scan</a> goes deeper and is credited toward a fix.</li></ol></div></section>
{faq_html(SC_FAQ)}''', [faq_ld(SC_FAQ)])

page("/newsletter/","Newsletter for AI Builders and Vibe Coders | Obrainsights",
 "A practical newsletter for vibe coders and AI builders: what breaks in AI-built apps, how to fix it, and useful agent setups.",
 f'''<section class="hero sm"><p class="eyebrow">Newsletter</p><h1>Ship it, <span class="accent">then make it hold.</span></h1><p class="lead">Practical notes for vibe coders and AI builders: what breaks in AI-built apps, how to fix it, launch checklists, and agent setups that work. No spam; unsubscribe anytime.</p></section>
<section class="narrow"><div class="card beehiiv-embed"><script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="118a4bdf-32cb-4e2b-8382-c0beb710ea12"></script><noscript><p>Subscribe at <a href="https://obrainsights.beehiiv.com/subscribe">obrainsights.beehiiv.com/subscribe</a>.</p></noscript></div><p class="muted small">Prefer a direct link? <a href="https://obrainsights.beehiiv.com/subscribe">Subscribe on Beehiiv</a>.</p></section>''')

page("/about/","About Obrainsights | Agent-Delivered, Human-Verified",
 "Obrainsights is an AI-agent-run productized services business, with human checkpoints for credentials, payments, and sign-off.",
 f'''<section class="hero sm"><p class="eyebrow">About</p><h1>An agent-run business, <span class="accent">with a human in the loop.</span></h1></section>
<section class="prose"><p>Obra Insights helps businesses and builders use AI as a tool to save time, resources, and effort. Human-led AI implementation for the real world: we take an idea, a prompt, or a half-broken AI-built app to a live, working product, then set up the AI agents that help run it.</p>
<p>The business is operated by AI agents that handle intake, scoping, delivery, QA, and follow-up. Our team brings the human touch into the loop. They approve custom quotes, refunds, access to production credentials, anything touching payments or personal data, and anything published under our name.</p>
<h2>How we work</h2><ul class="checks"><li>Fixed scopes and fixed prices, written before you pay.</li><li>Least-privilege, revocable access; credentials kept in a vault, never in chat or a repo.</li><li>Every change goes through a pull request you approve.</li><li>You own all accounts, domains, and code.</li><li>We're open about the agent model and show where humans check the work.</li></ul>
<p>This site was built with our own Launch Kit process.</p></section>''')

page("/contact/","Contact Obrainsights",
 "Request a Launch Kit, App Rescue, or Agent Setup, or ask a question. Every request gets a written fixed-price scope.",
 f'''<section class="hero sm"><p class="eyebrow">Contact</p><h1>Tell us what you're <span class="accent">building.</span></h1><p class="lead">Pick a service and describe where you are. You'll get a written scope and fixed price before any payment.</p><p class="lead">Prefer email? Write to <a href="mailto:info@obrainsights.com">info@obrainsights.com</a>.</p></section>
{PAID_FALLBACK}
<section class="narrow">{form("contact-form", CONTACT_ENDPOINT, [HONEYPOT, inp("name","Name"), inp("email","Email","email",ph="you@example.com"), sel("service","Interested in",["Prompt-to-Launch Kit","App Rescue: Health Scan","App Rescue: Quick Fix ($149)","App Rescue: Fix Sprint / Launch-Ready","Agent Setup Concierge","Agent retainer","Something else"]), inp("link","Link to app, repo, or idea doc","url",False,"https://"), ta("message","Message",True,"What do you have, and what do you need?")], "Send")}</section>''')


DRAFT = "<!-- DRAFT FOR OWNER REVIEW: not legal advice; confirm refund terms before launch. -->"
UPD = "October 16, 2026"
def legal_page(path, title, desc, h1, sections):
    body = f'<section class="hero sm"><p class="eyebrow">Legal (draft)</p><h1>{h1}</h1><p class="muted">Last updated: {UPD}. Draft pending review.</p></section><section class="prose">' + "".join(f"<h2>{e(h)}</h2>" + "".join(f"<p>{x}</p>" for x in ps) for h,ps in sections) + '<p>Questions: <a href="mailto:info@obrainsights.com">info@obrainsights.com</a>.</p></section>'
    page(path, title, desc, body, pre=DRAFT+"\n")
LLC = "Obrainsights, operated by Obra Ventures LLC"
legal_page("/terms/","Terms of Service | Obrainsights","Terms for Obrainsights services: Launch Kits, App Rescue, and Agent Setup.","Terms of <span class=\"accent\">Service</span>",[
 ("Who we are",[f'These terms are an agreement between you and {LLC}, a California limited liability company ("Obrainsights", "we"). By using obrainsights.com or buying a service, you agree to them.']),
 ("Services",["We offer fixed-scope productized services: the Prompt-to-Launch Kit, Vibe-Coded App Rescue, and Agent Setup Concierge, plus optional monthly retainers. Work is performed largely by AI agents and reviewed by a human. Each engagement is defined by a written scope agreed before payment; if the scope and these terms conflict, the written scope controls."]),
 ("Payments",["Prices are in USD and are paid upfront through Stripe. We never see or store your full card details; Stripe processes payments under its own terms and privacy policy. Retainers renew monthly until cancelled; you can cancel any time before the next billing date and keep service through the end of the paid period."]),
 ("Refunds",["If we have not started work, you can request a full refund. Once work has started, if we fail to deliver the agreed scope we will fix it or refund the undelivered portion. The $99 Health Scan is non-refundable once the report is delivered, but it is credited toward any Fix tier, including the $149 Quick Fix. Request refunds at info@obrainsights.com. [Confirm refund policy.]"]),
 ("Your responsibilities",["You confirm you have the right to share any code, accounts, or content you give us, and you grant us the limited, revocable access needed to do the work. You pay third-party fees (hosting, domains, model and API usage) directly."]),
 ("Ownership",["When you have paid in full, you own the deliverables, code, domains, and accounts we set up for you. We may reuse general know-how and non-confidential templates."]),
 ("Free scan and newsletter",["The free app scan is provided as-is and is limited to public URLs and repositories. It is not a full security audit. The newsletter is free and you can unsubscribe at any time."]),
 ("Disclaimers and liability",["Services are provided with reasonable skill, but we do not guarantee your app will be free of bugs or security issues. To the extent the law allows, our total liability for any claim is limited to the amount you paid us for the service in question, and we are not liable for indirect or consequential losses."]),
 ("Changes and governing law",["We may update these terms; the version in effect when you buy applies to that purchase. These terms are governed by the laws of the State of California, USA."]),
])
legal_page("/privacy/","Privacy Policy | Obrainsights","How Obrainsights collects and uses data from forms, the newsletter, payments, and hosting.","Privacy <span class=\"accent\">Policy</span>",[
 ("Who we are",[f"obrainsights.com is run by {LLC}, a California limited liability company. Contact us at info@obrainsights.com about anything in this policy."]),
 ("What we collect",["Contact and scan forms: your name, email, links you submit, and your message. Newsletter: your email and basic engagement data. Purchases: billing details handled by Stripe. Hosting: standard technical logs such as IP address and browser type."]),
 ("Service providers",['Form submissions are delivered to our inbox by email through <a href="https://resend.com/legal/privacy-policy">Resend</a>. The newsletter runs on <a href="https://www.beehiiv.com/privacy">Beehiiv</a>. Payments are processed by <a href="https://stripe.com/privacy">Stripe</a>; we never receive your full card number. The site is hosted on <a href="https://www.cloudflare.com/privacypolicy/">Cloudflare</a> Pages. Our email runs on Google Workspace. Each provider handles data under its own privacy policy.']),
 ("How we use it",["To reply to you, deliver and scope services, send the newsletter you signed up for, process payments, and keep the site secure. We do not sell your personal information."]),
 ("Retention",["We keep form and project records as long as needed to provide services and meet legal or tax obligations, then delete them. You can unsubscribe from the newsletter at any time with the link in every issue."]),
 ("Your choices",["You can ask us to access, correct, or delete your personal data by emailing info@obrainsights.com. Depending on where you live (for example California or the EU), you may have additional rights, and we will honor them."]),
 ("Children",["The site is not directed at children under 13, and we do not knowingly collect their data."]),
 ("Changes",["We will post updates here and change the date at the top."]),
])

# Blog
from blog_posts import POSTS as _P1
from blog_posts_2 import POSTS2 as _P2
POSTS = sorted(_P1 + _P2, key=lambda p: p["date"], reverse=True)  # newest first (stable within a date)
def nice_date(d):
    import datetime; return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
BLOG_CTA = '<section class="band card"><h2>Want a second pair of eyes on your app?</h2><p>Send us a public URL or repo. The free app scan checks for the common deploy, auth, and security problems and emails you what to fix first.</p><a class="btn" href="/scan/">Get a free app scan</a></section>'
for bp in POSTS:
    path = f"/blog/{bp['slug']}/"
    art = {"@type":"Article","headline":bp["title"],"description":bp["desc"],"datePublished":bp["date"],"dateModified":bp["date"],
           "author":{"@type":"Organization","name":"Obra Insights team","url":SITE+"/about/"},"publisher":{"@id":SITE+"/#org"},
           "mainEntityOfPage":{"@type":"WebPage","@id":SITE+path},"image":SITE+"/assets/og.png","inLanguage":"en"}
    crumbs = {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},{"@type":"ListItem","position":2,"name":"Blog","item":SITE+"/blog/"},{"@type":"ListItem","position":3,"name":bp["title"],"item":SITE+path}]}
    page(path, bp.get("seo", bp["title"]) + " | Obrainsights", bp["desc"],
     f'''<article><section class="hero sm"><p class="eyebrow"><a href="/blog/">Blog</a> · {bp["read"]}</p><h1>{bp["h1"]}</h1><p class="muted">By the Obra Insights team · <time datetime="{bp["date"]}">{nice_date(bp["date"])}</time></p></section>
<section class="prose">{bp["body"]}</section></article>{BLOG_CTA}''', [art, crumbs], og_type="article")
page("/blog/","Blog: Fixing and Launching AI-Built Apps | Obrainsights",
 "Practical guides for vibe coders: fixing broken Lovable, Bolt, Cursor, and Replit apps, getting them deployed, and launching them.",
 '<section class="hero sm"><p class="eyebrow">Blog</p><h1>Ship it, <span class="accent">fix it, launch it.</span></h1><p class="lead">Practical guides for getting AI-built apps from prompt to production.</p></section><section class="grid3">'
 + "".join(f'<a class="card svc" href="/blog/{bp["slug"]}/"><span class="tag">{bp["read"]}</span><h3>{e(bp["title"])}</h3><p>{e(bp["desc"])}</p></a>' for bp in POSTS)
 + '</section>' + BLOG_CTA,
 [{"@type":"Blog","name":"Obrainsights Blog","url":SITE+"/blog/","publisher":{"@id":SITE+"/#org"},
   "blogPost":[{"@type":"BlogPosting","headline":bp["title"],"url":f"{SITE}/blog/{bp['slug']}/","datePublished":bp["date"]} for bp in POSTS]}])

page("/thanks/","Payment received | Obrainsights","Thanks for your purchase. Here is what happens next.",
 f'''<section class="hero sm"><p class="eyebrow">Payment confirmed</p><h1>Payment received. <span class="accent">You're in.</span></h1>
<p class="lead" id="thanks-lead">Thanks for your purchase<span id="thanks-product"></span>. Your payment went through and your spot is reserved.</p></section>
<section class="grid2"><div class="card"><h2>What happens next</h2><ol class="steps">
<li><b>We'll email you within 1 business day</b> at the address you used at checkout, with a short intake and your written scope.</li>
<li><b>We confirm the details,</b> and your turnaround clock starts once intake is complete.</li>
<li><b>Agents do the work, a human verifies it,</b> and you get the delivery plus a plain-English handover.</li></ol></div>
<div class="card"><h2>What to have ready</h2><ul class="checks">
<li>A link to your app, repo, or idea doc.</li>
<li>A short description of the issue you want fixed or the idea you want launched.</li>
<li>Any deadlines, plus the domain you want to use if you have one.</li></ul>
<p class="muted small">Never email passwords or API keys. We'll set up secure, revocable access with you.</p></div></section>
<aside class="offer" id="thanks-credit" hidden><p id="thanks-credit-text"></p></aside>
<section class="band card"><h2>Questions?</h2><p>Reply to your Stripe receipt or write to <a href="mailto:info@obrainsights.com">info@obrainsights.com</a>. If you used code FOUNDING30, thank you for being a founding customer; we'll ask for a short testimonial after delivery.</p><a class="btn ghost" href="/">Back to home</a></section>
<script>(function(){{var P={json.dumps(PRODUCTS)};var s=new URLSearchParams(location.search).get("paid")||"";var n=P[s];
if(n){{document.getElementById("thanks-product").textContent=" of the "+n;document.title="Payment received: "+n+" | Obrainsights";}}
var c="";if(s==="rs-scan")c="Your $99 Health Scan is credited toward a fix: if the report shows something you want fixed, the $99 comes off a $149 Quick Fix, Fix Sprint, or Launch-Ready.";
else if(s==="rs-quickfix"||s==="rs-sprint"||s==="rs-launchready")c="Already bought a $99 Health Scan? Mention it when we email you and the $99 is credited toward this fix.";
if(c){{document.getElementById("thanks-credit-text").textContent=c;document.getElementById("thanks-credit").hidden=false;}}}})();</script>''', noindex=True)

# 404
page("/404.html","Page not found | Obrainsights","This page does not exist. Try the Obrainsights home page, pricing, or the free app scan for AI-built apps.",
 '<section class="hero sm"><h1>404: <span class="accent">nothing here.</span></h1><p class="lead">That page doesn\'t exist. Try the <a href="/">home page</a> or the <a href="/scan/">free app scan</a>.</p></section>')

# sitemap / robots / llms
LASTMOD = {f"/blog/{bp['slug']}/": bp["date"] for bp in POSTS}
LASTMOD.update({"/": "2026-10-17", "/pricing/": "2026-10-17", "/launch-kit/": "2026-10-17", "/rescue/": "2026-10-17", "/agents/": "2026-10-17", "/blog/": max(bp["date"] for bp in POSTS)})
paths = ["/","/launch-kit/","/rescue/","/agents/","/pricing/","/scan/","/newsletter/","/about/","/contact/","/terms/","/privacy/","/blog/"] + [f"/blog/{bp['slug']}/" for bp in POSTS]
open(os.path.join(OUT,"sitemap.xml"),"w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{LASTMOD.get(p, '2026-10-16')}</lastmod></url>\n" for p in paths) + "</urlset>\n")
open(os.path.join(OUT,"robots.txt"),"w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
def lt(rows): return "\n".join(f"- {a}: {b}. {c}. Turnaround: {d}." for a,b,c,d in rows)
open(os.path.join(OUT,"llms.txt"),"w").write(f"""# Obrainsights

> Obrainsights (obrainsights.com) is a productized services business for solo builders. It turns an idea, a prompt, or a half-broken vibe-coded app into a live, working product, then sets up AI agents to help run it. Work is delivered by AI agents and verified by a human. All prices are fixed, in USD, paid upfront, and currently marked as proposed launch pricing.

## Services
- [Prompt-to-Launch Kit]({SITE}/launch-kit/): one-page landing site on the customer's domain, waitlist, analytics, basic branding, launch copy.
- [Vibe-Coded App Rescue]({SITE}/rescue/): audit and fix of apps built with Cursor, Lovable, Bolt, Replit, v0, or Claude Code (deploy, auth, security, bugs, performance). Fixes delivered as pull requests.
- [Agent Setup Concierge]({SITE}/agents/): done-for-you single-job AI agents (Inbox Triage, Content Repurposing, Lead Research) on customer-owned accounts, plus monthly retainers.
- [Pricing]({SITE}/pricing/): all tiers.
- [Free App Scan]({SITE}/scan/): free limited scan of a public URL or repo, report by email.

## Prices
Prompt-to-Launch Kit:
{lt(LK_T)}

Vibe-Coded App Rescue:
{lt(RS_T)}

Agent Setup Concierge:
{lt(AG_T)}

Retainers (month-to-month; customer pays model/API usage directly):
{lt(RT_T)}

Rules: the $99 Scan fee is credited toward any Fix tier, including the $149 Quick Fix; Launch Kit buyers get $100 off a Rescue within 60 days; agent setups include one free month of Care; founding customer offer: 30% off any package for the first 10 clients in exchange for a short testimonial, using code FOUNDING30 at checkout or mentioning it on the written quote; work beyond a tier gets a fixed-price change order, never hourly billing.

## Policies
- Customers own all accounts, domains, and code.
- Least-privilege, revocable access; credentials are never stored in chat or repos.
- Every change goes through a pull request the customer approves.
- Full rebuilds and migrations are out of scope for App Rescue.

## Guides
{chr(10).join(f"- [{bp['title']}]({SITE}/blog/{bp['slug']}/): {bp['desc']}" for bp in POSTS)}

## Optional
- [About]({SITE}/about/)
- [Contact]({SITE}/contact/): email info@obrainsights.com
- [Newsletter]({SITE}/newsletter/)
- [Blog]({SITE}/blog/)
- [Terms]({SITE}/terms/)
- [Privacy]({SITE}/privacy/)
""")
# Static files: site/static/ is the source for brand assets + favicon.ico; copied into OUT on every build.
_here = os.path.dirname(os.path.abspath(__file__)); _pub = os.path.abspath(os.path.join(_here, "..", "public"))
if os.path.abspath(OUT) != _pub:  # preview/other outputs: bring along the hand-maintained files in public/
    shutil.copytree(os.path.join(_pub, "assets"), os.path.join(OUT, "assets"), dirs_exist_ok=True)
    shutil.copy2(os.path.join(_pub, "_headers"), os.path.join(OUT, "_headers"))
shutil.copytree(os.path.join(_here, "..", "static"), OUT, dirs_exist_ok=True)
print("built", len(paths)+1, "pages")
