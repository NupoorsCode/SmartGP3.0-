#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SmartGP static site build.

Produces a real multi-page site at directory URLs. Every public page ships its
full content in the initial HTML response, so nothing a crawler needs depends
on JavaScript running. The consultation, account and admin areas remain a
JavaScript app — they are behind a login, contain personal health data and are
marked noindex, so they have nothing to gain from being crawlable.

Run:  python3 src/build.py
Out:  site/
"""
import html
import json
import pathlib
import re
import shutil

from content import (ORIGIN, BRAND, NAV, FOOTER_NAV, EMERGENCY, TEAM, SERVICES,
                     COMPARE, FAQS, LEARN_CLUSTERS, LEARN_ARTICLES, RESOURCES,
                     TESTIMONIALS, CAREERS, LEGAL, COMMON, CHECKIN, BOOKING,
                     service, articles_in, person)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "site"

e = html.escape
INDEXABLE = []          # (path, priority, changefreq) for sitemap.xml


def money(n):
    n = float(n)
    return "\u00a3" + ("%d" % n if n == int(n) else "%.2f" % n)


# ---------------------------------------------------------------- templates

def fit_title(*variants):
    """Return the first variant 50-60 characters long, else the closest.

    Titles that are too short waste the slot; too long and Google truncates.
    Checking here means a new page cannot quietly ship outside the window.
    """
    for v in variants:
        if 50 <= len(v) <= 60:
            return v
    return min(variants, key=lambda v: abs(55 - len(v)))


def fit_desc(text, limit=160):
    """Trim to the last sentence or clause that fits inside the limit."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in (". ", "; ", ", "):
        i = cut.rfind(sep)
        if i > limit * 0.6:
            return cut[:i + 1].strip()
    return cut.rsplit(" ", 1)[0].rstrip(",;") + "."


def jsonld(obj):
    return ('<script type="application/ld+json">'
            + json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
            + "</script>")


def org_schema():
    return {
        "@context": "https://schema.org",
        "@type": ["MedicalBusiness", "Pharmacy"],
        "@id": ORIGIN + "/#organisation",
        "name": "SmartGP",
        "alternateName": "SmartGP Online Weight Loss Clinic",
        "url": ORIGIN + "/",
        "logo": ORIGIN + "/assets/img/smartgp-logo-960.png",
        "image": ORIGIN + "/assets/img/smartgp-logo-960.png",
        "description": ("SmartGP is a private online weight loss clinic for UK "
                        "patients. Every patient has a video consultation with a "
                        "UK-registered clinician before any medicine is prescribed. "
                        "Medicines are dispensed by SmartRx Pharmacy."),
        "medicalSpecialty": "https://schema.org/Nutrition",
        "areaServed": {"@type": "Country", "name": "United Kingdom"},
        "parentOrganization": {"@type": "Organization", "name": BRAND["company"]},
        "address": {"@type": "PostalAddress", "streetAddress": "10 Lyon Road",
                    "addressLocality": "London", "postalCode": "SW19 2RL",
                    "addressCountry": "GB"},
        "email": BRAND["email"],
        "availableLanguage": "en-GB",
    }


def website_schema():
    return {"@context": "https://schema.org", "@type": "WebSite",
            "@id": ORIGIN + "/#website", "url": ORIGIN + "/", "name": "SmartGP",
            "inLanguage": "en-GB",
            "publisher": {"@id": ORIGIN + "/#organisation"}}


def head(p):
    """p keys: title, desc, path, jsonld(list), noindex(bool), og_type, image."""
    canonical = ORIGIN + p["path"]
    robots = ("noindex, nofollow" if p.get("noindex")
              else "index, follow, max-image-preview:large, max-snippet:-1")
    blocks = "\n".join(jsonld(b) for b in p.get("jsonld", []))
    img = p.get("image", "/assets/img/smartgp-logo-960.png")
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(p['title'])}</title>
<meta name="description" content="{e(fit_desc(p['desc']))}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{p.get('og_type', 'website')}">
<meta property="og:site_name" content="SmartGP">
<meta property="og:locale" content="en_GB">
<meta property="og:title" content="{e(p['title'])}">
<meta property="og:description" content="{e(fit_desc(p['desc']))}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{ORIGIN}{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0E8C7F">
<link rel="icon" href="/assets/img/smartgp-logo-480.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/styles.css">
{blocks}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def header(active):
    items = "".join(
        '<li><a href="%s"%s>%s</a></li>'
        % (u, ' aria-current="page"' if active == u else "", e(t))
        for u, t in NAV)
    return f"""<div class="topbar">
  <div class="wrap topbar-in">
    <span class="topbar-mark">SmartRx Pharmacy</span>
    <span class="topbar-sep" aria-hidden="true"></span>
    <span class="topbar-txt">Dispensing and delivery by SmartRx &middot; GPhC registered</span>
    <a class="topbar-link" href="/about/">About the clinic</a>
  </div>
</div>

<header class="header">
  <div class="wrap header-in">
    <a class="logo" href="/">
      <img src="/assets/img/smartgp-logo-480.png"
           srcset="/assets/img/smartgp-logo-480.png 480w, /assets/img/smartgp-logo-960.png 960w"
           sizes="148px" width="148" height="41"
           alt="SmartGP — private online weight loss service">
    </a>
    <nav class="nav" aria-label="Primary"><ul style="display:flex;gap:4px;list-style:none;margin:0;padding:0">{items}</ul></nav>
    <div class="header-cta">
      <a class="btn btn-ghost" href="/account/">Log in</a>
      <a class="btn btn-solid" href="/consultation/">Start today</a>
      <button class="burger" id="burger" aria-label="Open menu" aria-expanded="false" aria-controls="mobilenav">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
  <nav class="mobilenav" id="mobilenav" aria-label="Primary, mobile">
    {"".join('<a href="%s">%s</a>' % (u, e(t)) for u, t in NAV)}
    <a href="/pricing/">Pricing</a>
    <a href="/about/team/">Meet the team</a>
    <a href="/account/">Log in</a>
    <a class="btn btn-solid" style="margin-top:14px" href="/consultation/">Start today</a>
  </nav>
</header>
"""


def crumbs(trail):
    """trail: [(url, label), ...] excluding Home, which is prepended.

    The visible breadcrumb and the BreadcrumbList structured data are generated
    from the same list, so they can never drift apart.
    """
    if not trail:
        return "", None
    full = [("/", "Home")] + list(trail)
    lis, items = [], []
    for i, (u, t) in enumerate(full):
        last = i == len(full) - 1
        lis.append('<li><span aria-current="page">%s</span></li>' % e(t) if last
                   else '<li><a href="%s">%s</a></li>' % (u, e(t)))
        items.append({"@type": "ListItem", "position": i + 1, "name": t,
                      "item": ORIGIN + u})
    nav = ('<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol>'
           + "".join(lis) + "</ol></div></nav>")
    return nav, {"@context": "https://schema.org", "@type": "BreadcrumbList",
                 "itemListElement": items}


def footer():
    cols = ""
    for headi, links in FOOTER_NAV:
        ls = "".join('<li><a href="%s">%s</a></li>' % (u, e(t)) for u, t in links)
        cols += '<div class="foot-col"><h2>%s</h2><ul>%s</ul></div>' % (e(headi), ls)
    b = BRAND
    return f"""<footer class="footer">
  <div class="wrap">
    <div class="foot-grid">

      <div class="foot-brand">
        <img src="/assets/img/smartgp-logo-960.png" width="150" height="42"
             alt="SmartGP" loading="lazy" class="foot-logo">
        <p>{e(b['blurb'])}</p>
        <p class="foot-people">
          <b>Owner:</b> {e(b['owner'])}<br>
          <b>Superintendent Pharmacist:</b> {e(b['superintendent'])}<br>
          (GPhC Number: {e(b['superintendent_reg'])})
        </p>
      </div>

      {cols}

      <div class="foot-col">
        <h2>Contact Us</h2>
        <ul class="foot-contact">
          <li><span class="fi" aria-hidden="true">&#9742;</span>
              <a href="tel:{e(b['phone_href'])}">{e(b['phone'])}</a></li>
          <li><span class="fi" aria-hidden="true">&#9993;</span>
              <a href="mailto:{e(b['email'])}">{e(b['email'])}</a></li>
          <li><span class="fi" aria-hidden="true">&#9200;</span>
              <span>{e(b['hours'])}</span></li>
          <li><span class="fi" aria-hidden="true">&#9679;</span>
              <address>{e(b['company'])}<br>10 Lyon Road, London SW19 2RL</address></li>
        </ul>
      </div>

    </div>

    <div class="foot-reg-row">
      <div class="foot-regbox">
        <p class="foot-regno">Registration No.: {e(b['gphc'])}</p>
        <a class="foot-verify" href="{e(b['gphc_url'])}"
           target="_blank" rel="noopener noreferrer">
          Verify registration status
          <span aria-hidden="true">&#8599;</span>
          <span class="visually-hidden">(opens the GPhC register in a new tab)</span>
        </a>
      </div>
      <p class="foot-emergency"><b>In an emergency call 999.</b><br>
        For urgent advice call NHS 111.</p>
    </div>
  </div>

  <div class="foot-bottom">
    <div class="wrap">
      <p>To check the registration status of the pharmacy or the Superintendent
        Pharmacist, please visit:<br>
        <a href="https://www.pharmacyregulation.org/registers"
           target="_blank" rel="noopener noreferrer">https://www.pharmacyregulation.org/registers</a></p>
      <p>&copy; Copyright {e(b['company'])} 2026. All rights reserved.
        Registered in England and Wales, company number {e(b['company_no'])}.</p>
      <p class="foot-proto">Prototype build &mdash; indicative content and prices, not for publication.</p>
    </div>
  </div>
</footer>

<div class="cookie" id="cookie" hidden></div>
<div class="toast" id="toast" hidden></div>
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def page(p, body, trail=None, active=None):
    crumb_html, crumb_ld = crumbs(trail or [])
    if crumb_ld:
        p.setdefault("jsonld", []).append(crumb_ld)
    return (head(p) + header(active) + crumb_html
            + '<main id="main">' + body + "</main>" + footer())


def write(path, content, priority=None, changefreq="monthly"):
    d = OUT / path.strip("/")
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(content, encoding="utf-8")
    if priority:
        INDEXABLE.append((path, priority, changefreq))


def sec(inner, cls=""):
    return '<section class="sec %s"><div class="wrap">%s</div></section>' % (cls, inner)


def emergency_panel(level=2):
    h = "h%d" % level
    return ('<div class="emergency"><%s>%s</%s><p style="font-weight:600;margin:8px 0 0">%s</p>'
            '<p class="small muted" style="margin:10px 0 0">This includes, but is not limited to:</p>'
            '<ul>%s</ul><p class="nhs">%s</p></div>'
            % (h, e(EMERGENCY["title"]), h, e(EMERGENCY["lead"]),
               "".join("<li>%s</li>" % e(i) for i in EMERGENCY["items"]),
               e(EMERGENCY["nhs"])))


def cluster_box(title, links):
    ls = "".join('<li><a href="%s">%s</a></li>' % (u, e(t)) for u, t in links)
    return ('<aside class="cluster"><h2>%s</h2><ul>%s</ul></aside>'
            % (e(title), ls))


# ==========================================================================
# 1. HOME
# ==========================================================================
def build_home():
    steps = [
        ("1", "Answer a few questions", "About 8 minutes. Honest answers, plain language."),
        ("2", "Book your video appointment", "Pick a slot. Nothing to pay."),
        ("3", "Meet your clinician", "They confirm your identity and weight, and decide with you."),
        ("4", "SmartRx sends a payment link", "Only if treatment is approved."),
        ("5", "Your medicine is delivered", "Cold chain where needed, tracked to your door."),
    ]
    marks = [
        ("Clinician-led", "Every decision is made by a registered clinician on a video call. Never by a form."),
        ("No basket", "Nothing is paid for until treatment has been approved. Payment is handled by SmartRx."),
        ("UK only", "UK addresses, UK mobile numbers, UK-licensed medicines, UK data hosting."),
    ]
    live = [s for s in SERVICES if s["published"] and s["kind"] != "service"][:3]

    body = f"""
<section class="hero">
  <div class="wrap hero-in">
    <div>
      <p class="eyebrow">Private online weight loss clinic &middot; United Kingdom</p>
      <h1>Say hello to a <em>new you</em></h1>
      <p class="hero-sub">Meet our online private weight loss service. A video
        consultation with a UK-registered clinician, and treatment dispensed by
        SmartRx if it is right for you.</p>
      <div class="btnrow">
        <a class="btn btn-solid" href="/consultation/">Start today</a>
        <a class="btn btn-ghost" href="/treatments/">See treatments and prices</a>
      </div>
      <div class="hero-marks">
        {"".join('<div class="hero-mark"><b>%s</b>%s</div>' % (e(a), e(b)) for a, b in marks)}
      </div>
    </div>
    <div class="heroCard">
      <div class="heroCard-h"><h2>How it works</h2><span>5 steps</span></div>
      {"".join('<div class="heroStep %s"><i>%s</i><div><b>%s</b><p>%s</p></div></div>'
               % ("is-off" if i > 2 else "", n, e(t), e(d))
               for i, (n, t, d) in enumerate(steps))}
      <div style="margin-top:18px;padding-top:16px;border-top:1px solid var(--line-2)">
        <a class="btn btn-quiet btn-sm" href="/consultation/">Begin step 1</a>
      </div>
    </div>
  </div>
</section>

<section class="sec sec-mint">
  <div class="wrap">
    <div class="sechead">
      <p class="eyebrow">Meet us</p>
      <h2>Our service is developed for you</h2>
      <p class="lead">Our mission is to make a difference and support you every step
        of the way &mdash; simplifying weight loss, and improving your health and
        wellness with solutions that support your journey.</p>
    </div>
    <div class="grid g3">
      <div class="card"><h3>A clinician decides</h3><p>Not a form, not a score, not an
        algorithm. Every approval, refusal and dose is a decision made by a registered
        clinician on a video call and recorded in your clinical record.</p></div>
      <div class="card"><h3>Nothing is sold first</h3><p>There is no basket on this
        site. You cannot buy a prescription medicine here. Payment happens only after
        treatment has been approved, and it is handled by SmartRx.</p></div>
      <div class="card"><h3>One pharmacy, end to end</h3><p>SmartRx dispenses, packs
        and delivers, using its own cold chain and courier accounts. Your prescription
        does not pass through a third party.</p></div>
    </div>
    <p style="margin-top:26px"><a href="/about/">Read more about the clinic and how it is regulated</a></p>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sechead">
      <p class="eyebrow">Optimised by medicine</p>
      <h2>The treatments a clinician may consider with you</h2>
      <p class="lead">Safely using our product knowledge, we support your journey with
        recommendations and advice at every step. Below is a factual comparison of the
        treatments a clinician may consider with you.</p>
    </div>
    <div class="tablewrap">
      <table>
        <caption class="visually-hidden">Weight loss treatments compared by type, frequency, cold chain and suitability</caption>
        <thead><tr>{"".join("<th scope=\"col\">%s</th>" % e(c) for c in COMPARE["columns"])}</tr></thead>
        <tbody>{"".join("<tr><th scope=\"row\">%s</th>%s</tr>"
                        % (e(r[0]), "".join("<td>%s</td>" % e(c) for c in r[1:]))
                        for r in COMPARE["rows"])}</tbody>
      </table>
    </div>
    <p class="small muted" style="margin-top:14px;max-width:70ch">{e(COMPARE["note"])}</p>
    <div class="btnrow" style="margin-top:22px">
      <a class="btn btn-solid" href="/treatments/">Read about each treatment</a>
      <a class="btn btn-ghost" href="/pricing/">See prices per dosage</a>
    </div>
  </div>
</section>

<section class="sec sec-mint">
  <div class="wrap">
    <div class="sechead"><p class="eyebrow">Stories and support</p>
      <h2>Join our weight loss community</h2></div>
    <div class="grid g3">
      {"".join('''<article class="card card-link"><h3><a href="/learn/%s/">%s</a></h3>
        <p>%s</p></article>''' % (c["slug"], e(c["title"]), e(c["intro"]))
               for c in LEARN_CLUSTERS)}
    </div>
    <p style="margin-top:24px"><a href="/learn/">Browse everything in Learn</a>
      &middot; <a href="/support/">Read the FAQs</a>
      &middot; <a href="/support/patient-resources/">Patient resources</a></p>
  </div>
</section>

<section class="sec sec-ink">
  <div class="wrap" style="display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center">
    <div>
      <p class="eyebrow">Learn more about weight loss</p>
      <h2>Sign up to our newsletter</h2>
      <p class="lead">Be first to receive new information, recipes, industry news and insights.</p>
    </div>
    <div>
      <form class="newsletter" data-newsletter>
        <label class="visually-hidden" for="nl">Email address</label>
        <input type="email" id="nl" name="email" placeholder="Enter your email" required>
        <button class="btn btn-solid" type="submit">Sign up</button>
      </form>
      <p class="small" style="margin-top:12px;color:#82A49C">Marketing consent is
        recorded separately from service messages about your appointments.
        Unsubscribe in one click, honoured immediately.</p>
    </div>
  </div>
</section>
"""
    write("/", page({
        "title": "Online weight loss clinic UK | Video consultation | SmartGP",
        "desc": "Say hello to a new you. A private UK online weight loss clinic: "
                "video consultation with a registered clinician before anything is "
                "prescribed.",
        "path": "/",
        "jsonld": [org_schema(), website_schema()],
    }, body, trail=None, active=None), priority="1.0", changefreq="weekly")


# ==========================================================================
# 2. TREATMENTS HUB + DETAIL
# ==========================================================================
def tcard(s):
    avail = any(x["available"] for x in s["strengths"])
    kind = ("Consultation" if s["kind"] == "service"
            else "Tablet" if s["kind"] == "oral" else "Injection")
    return f"""<article class="tcard">
  <div class="tcard-top">
    <span class="tag {'tag-teal' if s['kind'] == 'service' else 'tag-ok'}">{kind}</span>
    <span class="tag {'tag-ok' if avail else 'tag-off'}">{'Available' if avail else 'Unavailable'}</span>
  </div>
  <div class="tcard-body">
    <h3><a href="/treatments/{s['id']}/">{e(s['name'])}</a></h3>
    <p style="color:var(--ink-3);font-size:.86rem;margin-bottom:8px">{e(s['strapline'])}</p>
    <p>{e(s['blurb'])}</p>
    <ul class="strengths">{"".join('<li class="strength %s">%s</li>'
                                   % ("" if x["available"] else "off", e(x["label"]))
                                   for x in s["strengths"])}</ul>
    <p class="small muted" style="margin-top:10px">No subscription needed.</p>
  </div>
  <div class="tcard-foot">
    <p class="tcard-price" style="margin:0">{money(s['price_from'])}<small>from &middot; includes consultation</small></p>
    <a class="btn btn-solid btn-sm" href="/treatments/{s['id']}/">Read about {e(s['short'])}</a>
  </div>
</article>"""


def build_treatments():
    body = sec(f"""
<h1>Weight loss treatments</h1>
<p class="lead">Choose the treatment you would like to discuss. Reading about it is
the first step of the consultation &mdash; there is no basket and nothing to pay here.</p>
<div class="notice notice-info" style="max-width:70ch;margin-top:26px">
  <h2>Every treatment needs a video consultation</h2>
  <p style="margin:0">Weight loss medicines cannot be supplied on the basis of an
  online questionnaire alone, so a clinician always sees you before anything is
  prescribed.</p>
</div>

<h2 style="margin-top:44px">Compare the treatments</h2>
<div class="grid g3" style="margin-top:20px">{"".join(tcard(s) for s in SERVICES if s["published"])}</div>

<h2>How a clinician chooses with you</h2>
<p style="max-width:70ch">That is a conversation, not a filter on this page. Your
clinician weighs up your medical history, anything you already take, how you would
feel about a weekly injection, and what you have tried before.</p>
<p><a href="/pricing/">See the price of every strength</a> &middot;
   <a href="/learn/glp-1-medicines/">Understand how GLP-1 medicines work</a> &middot;
   <a href="/about/team/">Meet the clinicians who will see you</a></p>
""")
    write("/treatments/", page({
        "title": "Weight loss treatments | Mounjaro and Wegovy | SmartGP",
        "desc": "Compare the weight loss treatments SmartGP prescribes: Mounjaro, "
                "Wegovy and Orlistat. All require a video consultation with a UK "
                "clinician.",
        "path": "/treatments/",
        "jsonld": [{
            "@context": "https://schema.org", "@type": "CollectionPage",
            "name": "Weight loss treatments", "url": ORIGIN + "/treatments/",
            "isPartOf": {"@id": ORIGIN + "/#website"},
            "about": {"@type": "MedicalCondition", "name": "Obesity"},
        }],
    }, body, trail=[("/treatments/", "Treatments")], active="/treatments/"),
        priority="0.9", changefreq="weekly")

    for s in SERVICES:
        build_treatment(s)


def build_treatment(s):
    def block(t, arr, hid):
        return ("<h2 id=\"%s\">%s</h2><ul>%s</ul>"
                % (hid, e(t), "".join("<li>%s</li>" % e(x) for x in arr)))

    rows = "".join(
        '<tr><th scope="row">%s</th><td>%s</td><td class="num">%s</td></tr>'
        % (e(x["label"]),
           '<span class="tag tag-ok">Available</span>' if x["available"]
           else '<span class="tag tag-off">Currently unavailable</span>',
           money(x["price"]))
        for x in s["strengths"])

    price_table = f"""<div class="tablewrap" style="margin:18px 0">
  <table>
    <caption>{e(s['name'])} &mdash; price by strength</caption>
    <thead><tr><th scope="col">Strength or pack</th><th scope="col">Availability</th>
      <th scope="col" class="num">Price</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    related = [a for a in LEARN_ARTICLES if s["id"] in a.get("related_treatments", [])][:3]
    others = [x for x in SERVICES if x["id"] != s["id"] and x["published"]][:3]
    cluster_links = ([("/learn/%s/%s/" % (a["cluster"], a["slug"]), a["title"]) for a in related]
                     + [("/treatments/%s/" % o["id"], o["name"]) for o in others]
                     + [("/pricing/", "Compare every price"),
                        ("/support/", "Questions patients ask before booking")])

    verify_note = ""
    if s.get("verify"):
        verify_note = ('<div class="notice notice-flag"><h2>Product naming to confirm</h2>'
                       '<p style="margin:0">The brand and formulation shown here must be '
                       'confirmed clinically and commercially before publication '
                       '(BRD Appendix D). Do not publish this page until Rachel Wood '
                       'and Josh Cocklin have signed it off.</p></div>')

    offers = [{"@type": "Offer", "name": "%s %s" % (s["name"], x["label"]),
               "price": str(x["price"]), "priceCurrency": "GBP",
               "availability": ("https://schema.org/InStock" if x["available"]
                                else "https://schema.org/OutOfStock"),
               "url": ORIGIN + "/treatments/%s/" % s["id"],
               "eligibleCustomerType": "https://schema.org/Patient"}
              for x in s["strengths"]]

    ld = [{
        "@context": "https://schema.org", "@type": "MedicalWebPage",
        "url": ORIGIN + "/treatments/%s/" % s["id"],
        "name": s["meta_title"], "inLanguage": "en-GB",
        "lastReviewed": "2026-08-19",
        "reviewedBy": {"@type": "Person", "name": "Rachel Wood",
                       "jobTitle": "Independent Prescriber",
                       "url": ORIGIN + "/about/team/rachel-wood/"},
        "audience": {"@type": "Patient"},
        "isPartOf": {"@id": ORIGIN + "/#website"},
        "publisher": {"@id": ORIGIN + "/#organisation"},
    }]
    if s["kind"] != "service":
        ld.append({
            "@context": "https://schema.org", "@type": "Drug",
            "name": s["name"], "activeIngredient": s.get("inn") or s["name"],
            "prescriptionStatus": "https://schema.org/PrescriptionOnly",
            "url": ORIGIN + "/treatments/%s/" % s["id"],
            "offers": offers,
            "warning": ("%s is a prescription-only medicine. It can only be "
                        "prescribed after a video consultation with a registered "
                        "clinician who independently verifies your height and "
                        "weight. Not suitable during pregnancy or breastfeeding, "
                        "or for people under 18." % s["name"]),
        })

    kind_label = ("Consultation" if s["kind"] == "service"
                  else "Weekly injection" if s["kind"] == "injection" else "Daily tablet")

    body = sec(f"""
<div style="display:grid;grid-template-columns:1.4fr .9fr;gap:52px;align-items:start" class="tsplit">
  <div>
    <p class="eyebrow">{kind_label}</p>
    <h1 style="font-size:clamp(2rem,4vw,3rem)">{e(s['name'])}</h1>
    <p class="lead">{e(s['blurb'])}</p>

    {verify_note}

    <div class="notice notice-info">
      <h2>Prescription-only medicine</h2>
      <p style="margin:0">{e(s['name'])} can only be prescribed after a video
      appointment with one of our clinicians, who must independently confirm your
      height and weight. We cannot prescribe it from your answers alone.</p>
    </div>

    <div class="prose">
      {block('Is it suitable for me?', s['info']['suitable'], 'suitable')}
      {block('How do I use it?', s['info']['how'], 'how')}
      {block('How does it work?', s['info']['works'], 'works')}
      <h2 id="prices">Strengths and prices</h2>
      <p>Your clinician decides which strength you start on &mdash; almost always the
      lowest &mdash; and whether to increase it later. You are never charged for a
      strength you have not been prescribed.</p>
      {price_table}
      <p class="small muted">Every price includes your video appointment, the medicine,
      the needles you need where relevant, and tracked delivery. There is no
      subscription and no separate consultation fee.</p>
      {block('Other important information', s['info']['other'], 'other')}
    </div>

    <div class="reviewed">
      <b>Clinically reviewed</b> by Rachel Wood, Independent Prescriber, on
      19 August 2026. Next review due August 2027. This page is information, not a
      recommendation &mdash; whether this treatment suits you is a decision for you
      and your clinician together.
    </div>
  </div>

  <aside class="card" style="position:sticky;top:100px">
    <h2 style="font-family:var(--f-body);font-size:1rem;font-weight:700">At a glance</h2>
    <dl style="font-size:.9rem;margin:0">
      <dt style="font-weight:700;margin-top:10px">Cost</dt>
      <dd style="margin:0">{money(s['price_from'])} to {money(s['strengths'][-1]['price'])}, all included</dd>
      <dt style="font-weight:700;margin-top:10px">Strengths</dt>
      <dd style="margin:0">{len(s['strengths'])}</dd>
      <dt style="font-weight:700;margin-top:10px">Prescribed by</dt>
      <dd style="margin:0">A UK-registered clinician, after a video appointment</dd>
      <dt style="font-weight:700;margin-top:10px">Dispensed by</dt>
      <dd style="margin:0">SmartRx Pharmacy, 10 Lyon Road, London SW19 2RL</dd>
    </dl>
    <a class="btn btn-solid" style="width:100%;margin-top:16px" href="/consultation/?treatment={s['id']}">Start consultation</a>
    <a class="btn btn-ghost btn-sm" style="width:100%;margin-top:8px" href="/treatments/">Compare other treatments</a>
  </aside>
</div>
<style>@media(max-width:900px){{.tsplit{{grid-template-columns:1fr !important;gap:28px !important}}.tsplit aside{{position:static !important}}}}</style>

{cluster_box("Related reading", cluster_links)}
""")
    write("/treatments/%s/" % s["id"], page(
        {"title": s["meta_title"], "desc": s["meta_desc"],
         "path": "/treatments/%s/" % s["id"], "jsonld": ld},
        body,
        trail=[("/treatments/", "Treatments"), ("/treatments/%s/" % s["id"], s["short"])],
        active="/treatments/"), priority="0.9", changefreq="weekly")


# ==========================================================================
# 3. PRICING
# ==========================================================================
def build_pricing():
    tables = ""
    for s in SERVICES:
        rows = "".join(
            '<tr><th scope="row">%s</th><td class="num">%s</td><td>%s</td></tr>'
            % (e(x["label"]), money(x["price"]),
               '<span class="tag tag-ok">Available</span>' if x["available"]
               else '<span class="tag tag-off">Currently unavailable</span>')
            for x in s["strengths"])
        note = ("The appointment only. No medicine is supplied."
                if s["kind"] == "service"
                else "Consultation, review, medicine and delivery included.")
        tables += f"""
<h2 id="{s['id']}">{e(s['name'])}</h2>
<p class="small muted">{e(note)} <a href="/treatments/{s['id']}/">About {e(s['short'])}</a></p>
<div class="tablewrap" style="margin-bottom:34px">
  <table>
    <caption class="visually-hidden">{e(s['name'])} price by strength or pack</caption>
    <thead><tr><th scope="col">Strength or pack</th><th scope="col" class="num">Price</th>
      <th scope="col">Availability</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    body = sec(f"""
<h1>Pricing</h1>
<p class="lead">The price for each strength of each treatment, what is included, and
when you pay. Shown factually &mdash; not a promotion and not a recommendation.</p>
<p style="max-width:70ch">The <a href="/treatments/">treatments page</a> compares
treatments by type, frequency and who they suit. This page shows the price of each
individual strength or pack size.</p>

{tables}

<h2>What you are not charged for</h2>
<ul style="max-width:70ch">
  <li>Registering, or starting a consultation you do not finish.</li>
  <li>An appointment where the clinician decides treatment is not right for you.</li>
  <li>The review appointment needed before each repeat.</li>
  <li>Reporting a side effect, or asking a question about your treatment.</li>
</ul>

<h2>When you pay</h2>
<p style="max-width:70ch">Nothing at booking. If your clinician approves treatment,
SmartRx sends one payment link covering everything. The advice-only appointment is
the exception &mdash; that fee is paid when you book, because there is no product
order for SmartRx to bill against.</p>

<h2>Refunds</h2>
<p style="max-width:70ch">Dispensed medicines are exempt from the 14-day
distance-selling cancellation right for safety reasons. Refunds, where due, are
processed by SmartRx. See the <a href="/legal/terms/">terms and conditions</a>.</p>

<p class="small muted" style="margin-top:28px;max-width:74ch">Prices are indicative
and must be confirmed before publication. All prices in GBP. Clinical assessment is
required before any medicine can be supplied.</p>
""")
    write("/pricing/", page({
        "title": fit_title("Weight loss treatment prices, every strength | SmartGP"),
        "desc": "Every SmartGP price listed before you register. Mounjaro from "
                "\u00a3149 and Wegovy from \u00a3139, including your video appointment, "
                "medicine and tracked delivery.",
        "path": "/pricing/",
        "jsonld": [{"@context": "https://schema.org", "@type": "WebPage",
                    "name": "Pricing", "url": ORIGIN + "/pricing/",
                    "isPartOf": {"@id": ORIGIN + "/#website"}}],
    }, body, trail=[("/pricing/", "Pricing")], active="/treatments/"),
        priority="0.9", changefreq="weekly")


# ==========================================================================
# 4. LEARN — hub, cluster hubs, articles
# ==========================================================================
def build_learn():
    clusters = ""
    for c in LEARN_CLUSTERS:
        arts = articles_in(c["slug"])
        items = "".join(
            '<li><a href="/learn/%s/%s/">%s</a></li>' % (c["slug"], a["slug"], e(a["title"]))
            for a in arts)
        clusters += f"""<article class="card">
  <h3><a href="/learn/{c['slug']}/">{e(c['title'])}</a></h3>
  <p>{e(c['intro'])}</p>
  <ul style="padding-left:18px;font-size:.92rem">{items}</ul>
</article>"""

    body = sec(f"""
<h1>Learn about weight loss</h1>
<p class="lead">Plain-English articles about treatment, food, movement and side
effects. Every article names the clinician who wrote it and the clinician who
reviewed it, and carries the date it was last checked.</p>

<h2 style="margin-top:40px">Browse by topic</h2>
<div class="grid g3" style="margin-top:20px">{clusters}</div>

<div class="card" style="margin-top:44px;background:var(--mint-2)">
  <h2 style="font-family:var(--f-body);font-size:1.1rem;font-weight:700">Sign up to our newsletter</h2>
  <p>New information, recipes, industry news and insights.</p>
  <form class="newsletter" data-newsletter>
    <label class="visually-hidden" for="nl2">Email address</label>
    <input type="email" id="nl2" name="email" placeholder="Enter your email" required>
    <button class="btn btn-solid" type="submit">Sign up</button>
  </form>
</div>
""")
    write("/learn/", page({
        "title": "Learn about weight loss and GLP-1 medicines | SmartGP",
        "desc": "Clinician-written guides on GLP-1 medicines, side effects, eating "
                "well and keeping muscle during weight loss. Each article is dated "
                "and clinically reviewed.",
        "path": "/learn/",
        "jsonld": [{"@context": "https://schema.org", "@type": "CollectionPage",
                    "name": "Learn about weight loss", "url": ORIGIN + "/learn/",
                    "isPartOf": {"@id": ORIGIN + "/#website"}}],
    }, body, trail=[("/learn/", "Learn")], active="/learn/"),
        priority="0.7", changefreq="weekly")

    for c in LEARN_CLUSTERS:
        build_cluster(c)
        for a in articles_in(c["slug"]):
            build_article(c, a)


def build_cluster(c):
    arts = articles_in(c["slug"])
    cards = "".join(f"""<article class="card">
  <h3><a href="/learn/{c['slug']}/{a['slug']}/">{e(a['title'])}</a></h3>
  <p>{e(a['standfirst'])}</p>
  <p class="small muted" style="margin:0">Reviewed {e(a['updated'])}</p>
</article>""" for a in arts)

    others = [("/learn/%s/" % x["slug"], x["title"]) for x in LEARN_CLUSTERS if x["slug"] != c["slug"]]
    body = sec(f"""
<h1>{e(c['title'])}</h1>
<p class="lead">{e(c['intro'])}</p>
<h2 style="margin-top:36px">Articles in this topic</h2>
<div class="grid g3" style="margin-top:20px">{cards}</div>
{cluster_box("Other topics", others + [("/treatments/", "See the treatments"), ("/support/", "Frequently asked questions")])}
""")
    write("/learn/%s/" % c["slug"], page({
        "title": c["meta_title"], "desc": c["meta_desc"],
        "path": "/learn/%s/" % c["slug"],
        "jsonld": [{"@context": "https://schema.org", "@type": "CollectionPage",
                    "name": c["title"], "url": ORIGIN + "/learn/%s/" % c["slug"],
                    "isPartOf": {"@id": ORIGIN + "/#website"}}],
    }, body, trail=[("/learn/", "Learn"), ("/learn/%s/" % c["slug"], c["title"])],
        active="/learn/"), priority="0.7", changefreq="monthly")


def build_article(c, a):
    au, rv = person(a["author"]), person(a["reviewer"])
    toc = "".join('<li><a href="#%s">%s</a></li>' % (sid, e(t)) for sid, t, _ in a["sections"])
    secs = "".join(
        '<h2 id="%s">%s</h2>%s' % (sid, e(t), "".join("<p>%s</p>" % e(p) for p in paras))
        for sid, t, paras in a["sections"])
    refs = "".join("<li>%s</li>" % e(r) for r in a["refs"])

    siblings = [("/learn/%s/%s/" % (c["slug"], x["slug"]), x["title"])
                for x in articles_in(c["slug"]) if x["slug"] != a["slug"]]
    treats = [("/treatments/%s/" % t, service(t)["name"])
              for t in a.get("related_treatments", []) if service(t)]

    path = "/learn/%s/%s/" % (c["slug"], a["slug"])
    ld = [{
        "@context": "https://schema.org", "@type": "MedicalWebPage",
        "url": ORIGIN + path, "headline": a["title"], "name": a["title"],
        "description": a["meta_desc"], "inLanguage": "en-GB",
        "datePublished": a["published"], "dateModified": a["updated"],
        "lastReviewed": a["updated"],
        "author": {"@type": "Person", "name": au["name"], "jobTitle": au["role"],
                   "url": ORIGIN + "/about/team/%s/" % au["slug"]},
        "reviewedBy": {"@type": "Person", "name": rv["name"], "jobTitle": rv["role"],
                       "url": ORIGIN + "/about/team/%s/" % rv["slug"]},
        "publisher": {"@id": ORIGIN + "/#organisation"},
        "isPartOf": {"@id": ORIGIN + "/#website"},
        "audience": {"@type": "Patient"},
        "about": {"@type": "MedicalCondition", "name": "Obesity"},
    }]

    body = sec(f"""
<article class="prose" style="max-width:none">
  <div style="max-width:70ch">
    <p class="eyebrow">{e(c['title'])}</p>
    <h1>{e(a['title'])}</h1>
    <p class="lead">{e(a['standfirst'])}</p>

    <div class="byline">
      <span class="byline-av" aria-hidden="true">{e(au['initials'])}</span>
      <p class="byline-txt" style="margin:0">
        Written by <a href="/about/team/{au['slug']}/"><b>{e(au['name'])}</b></a>, {e(au['role'])}.<br>
        Clinically reviewed by <a href="/about/team/{rv['slug']}/">{e(rv['name'])}</a>, {e(rv['role'])}.
        <span class="byline-dates">Published {e(a['published'])} &middot; Last reviewed {e(a['updated'])} &middot; Next review {e(a['next_review'])}</span>
      </p>
    </div>

    <nav class="toc" aria-labelledby="toc-h">
      <h2 id="toc-h">On this page</h2>
      <ol>{toc}</ol>
    </nav>

    {secs}

    <div class="notice notice-info" style="margin-top:34px">
      <h2>This is information, not advice about you</h2>
      <p style="margin:0">Whether any treatment is right for you is a decision for you
      and your clinician together, at your appointment.</p>
    </div>

    <section class="refs">
      <h2>Sources</h2>
      <ol>{refs}</ol>
      <p class="small muted">Citations are placeholders pending clinical sign-off.
      Live links must be checked and approved before publication.</p>
    </section>
  </div>

  {cluster_box("More in " + c["title"], siblings + treats + [("/learn/" + c["slug"] + "/", "All " + c["title"].lower() + " articles")])}
</article>
""")
    write(path, page({
        "title": a["meta_title"], "desc": a["meta_desc"], "path": path,
        "og_type": "article", "jsonld": ld,
    }, body, trail=[("/learn/", "Learn"), ("/learn/%s/" % c["slug"], c["title"]),
                    (path, a["title"])], active="/learn/"),
        priority="0.6", changefreq="monthly")


# ==========================================================================
# 5. SUPPORT + RESOURCES
# ==========================================================================
def build_support():
    groups = []
    for g, q, ans in FAQS:
        if not groups or groups[-1][0] != g:
            groups.append((g, []))
        groups[-1][1].append((q, ans))

    blocks = ""
    for g, items in groups:
        blocks += "<h2>%s</h2>" % e(g)
        blocks += "".join(
            '<details class="faq" data-q="%s"><summary>%s</summary>'
            '<div class="faq-body"><p>%s</p></div></details>'
            % (e((q + " " + a).lower()), e(q), e(a)) for q, a in items)

    body = sec(f"""
<h1>Support: questions and advice</h1>
<p class="lead">Answers to the questions patients ask most often. If yours is not
here, <a href="/contact/">contact us</a> &mdash; we would rather answer it than have
you guess.</p>

<div class="field" style="max-width:460px;margin-top:26px">
  <label class="field-label" for="faqq">Search the questions</label>
  <input id="faqq" type="search" placeholder="e.g. delivery, payment, side effects" data-faqsearch>
</div>

<div id="faqlist">{blocks}</div>

<div class="card" style="margin-top:40px;display:flex;gap:20px;align-items:center;flex-wrap:wrap">
  <div style="flex:1;min-width:240px"><h2 style="font-family:var(--f-body);font-size:1.05rem;font-weight:700">Still stuck?</h2>
    <p style="margin:0">Contact the clinic and we will come back to you within one working day.</p></div>
  <a class="btn btn-solid" href="/contact/">Contact us</a>
</div>

{cluster_box("Useful next steps", [
    ("/support/patient-resources/", "Patient resources"),
    ("/treatments/", "See the treatments"),
    ("/pricing/", "Check the prices"),
    ("/learn/side-effects/", "Read about side effects"),
])}
""")
    write("/support/", page({
        "title": fit_title("Support: common questions about our service | SmartGP"),
        "desc": "Common questions about SmartGP's online weight loss service: video "
                "consultations, when you pay, ID checks, repeats, delivery, refunds "
                "and privacy.",
        "path": "/support/",
        "jsonld": [{
            "@context": "https://schema.org", "@type": "FAQPage",
            "url": ORIGIN + "/support/",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for _g, q, a in FAQS],
        }],
    }, body, trail=[("/support/", "Support")], active="/support/"),
        priority="0.8", changefreq="monthly")

    cards = "".join('<div class="card"><h3>%s</h3><p>%s</p></div>' % (e(t), e(d))
                    for t, d in RESOURCES)
    rbody = sec(f"""
<h1>Patient resources</h1>
<p class="lead">Practical guidance for people already using treatment.</p>
<h2 style="margin-top:36px">Guides</h2>
<div class="grid g3" style="margin-top:20px">{cards}</div>
<div class="notice notice-flag" style="margin-top:34px;max-width:74ch">
  <h2>Report a suspected side effect</h2>
  <p style="margin:0">Use the side effect form in your account so the clinic is
  alerted, and report it to the MHRA through the Yellow Card scheme. Reporting helps
  identify problems that trials do not catch.</p>
</div>
{cluster_box("Related", [
    ("/learn/side-effects/", "Side effects explained"),
    ("/learn/glp-1-medicines/", "How GLP-1 medicines work"),
    ("/support/", "Frequently asked questions"),
    ("/contact/", "Contact the clinic"),
])}
""")
    write("/support/patient-resources/", page({
        "title": "Patient resources: injections, storage, safety | SmartGP",
        "desc": "Injection technique, cold chain storage, side effect guidance, diet "
                "and activity support, and how to report to the MHRA Yellow Card scheme.",
        "path": "/support/patient-resources/",
    }, rbody, trail=[("/support/", "Support"),
                     ("/support/patient-resources/", "Patient resources")],
        active="/support/"), priority="0.6", changefreq="monthly")


# ==========================================================================
# 6. ABOUT / TEAM / TESTIMONIALS / CAREERS
# ==========================================================================
def build_about():
    b = BRAND
    body = sec(f"""
<h1>About SmartGP</h1>
<p class="lead">SmartGP is a private online weight loss clinic for UK patients, built
on an established pharmacy rather than bolted onto one.</p>

<div class="prose">
  <h2>Who we are</h2>
  <p>SmartGP is a trading name of {e(b['company'])}. It is an evolution of SmartRx,
  the online pharmacy service that dispenses and delivers every medicine prescribed
  here. That matters practically: your prescription does not pass through a
  third-party fulfilment company, and the pharmacy that supplies it is the same one
  whose registration appears at the bottom of this page.</p>

  <h2>How we work</h2>
  <p>Two principles govern everything on this site. A clinician decides, never the
  system &mdash; the questionnaire gathers and flags information, and never approves,
  rejects or triages anyone. And nothing is sold before that decision: there is no
  basket, and payment happens only after a clinician has approved treatment.</p>

  <h2>How we are regulated</h2>
  <p>The pharmacy is registered with the General Pharmaceutical Council, and you can
  check that registration yourself on the
  <a href="https://www.pharmacyregulation.org/registers" rel="noopener">public register</a>
  before you book. Our Superintendent Pharmacist is named in the footer of every
  page, as is the registered company and its office. Prescribing clinicians are
  registered with the GPhC, GMC or NMC.</p>
  <p>Weight loss medicines cannot be supplied on the basis of an online questionnaire
  alone. Height and weight must be independently verified before a first supply,
  either on the video call or by timestamped photographic evidence. That requirement
  is why this service is built around an appointment rather than a form.</p>

  <h2>What we do not do</h2>
  <ul>
    <li>We do not advertise prescription-only medicines. Product information appears
      only inside a consultation-led journey.</li>
    <li>We do not run discounts, subscriptions, referral incentives or urgency
      messaging on prescription medicines.</li>
    <li>We do not publish before-and-after imagery or outcome claims.</li>
    <li>We are not an emergency service, and we cannot respond urgently.</li>
  </ul>
</div>

{cluster_box("Read more", [
    ("/about/team/", "Meet the clinicians"),
    ("/about/testimonials/", "What patients say"),
    ("/treatments/", "Treatments we prescribe"),
    ("/legal/privacy/", "How we handle your data"),
])}
""")
    write("/about/", page({
        "title": fit_title("About SmartGP | How our online weight clinic works"),
        "desc": "Who runs SmartGP, how the clinic is regulated by the GPhC, and the "
                "two principles behind the service: a clinician always decides, and "
                "nothing is sold first.",
        "path": "/about/",
        "jsonld": [{"@context": "https://schema.org", "@type": "AboutPage",
                    "url": ORIGIN + "/about/",
                    "mainEntity": {"@id": ORIGIN + "/#organisation"}}],
    }, body, trail=[("/about/", "About")], active=None),
        priority="0.7", changefreq="monthly")

    build_team()
    build_testimonials()
    build_careers()


def build_team():
    cards = "".join(f"""<li class="card person">
  <div class="person-img" aria-hidden="true">{e(p['initials'])}</div>
  <h3><a href="/about/team/{p['slug']}/">{e(p['name'])}</a></h3>
  <p class="role">{e(p['role'])}</p>
  <p>{e(p['about'])}</p>
  <p class="small muted" style="margin:0">{e(p['reg'])}</p>
</li>""" for p in TEAM)

    body = sec(f"""
<h1>Meet the team</h1>
<p class="lead">The people responsible for your care and for how this service is run.
Every clinician is named, registered, and checkable on a public register before you book.</p>

<h2 style="margin-top:36px">Our clinicians</h2>
<ul class="people grid g3" style="margin-top:20px">{cards}</ul>

<div class="notice notice-info" style="margin-top:34px;max-width:70ch">
  <h2>You do not choose your clinician</h2>
  <p style="margin:0">Whichever clinician is available attends your appointment.
  Assignment is handled inside the clinic so that slots stay open and waits stay
  short. Both prescribers work to the same clinical protocols.</p>
</div>
""")
    write("/about/team/", page({
        "title": fit_title("Meet the team: our registered clinicians | SmartGP"),
        "desc": "The named, registered clinicians who see SmartGP patients and sign "
                "off our clinical content. Check their registration before you book.",
        "path": "/about/team/",
        "jsonld": [{"@context": "https://schema.org", "@type": "WebPage",
                    "name": "Meet the team", "url": ORIGIN + "/about/team/",
                    "isPartOf": {"@id": ORIGIN + "/#website"},
                    "mainEntity": [{"@type": "Person", "name": p["name"],
                                    "jobTitle": p["role"],
                                    "url": ORIGIN + "/about/team/%s/" % p["slug"],
                                    "worksFor": {"@id": ORIGIN + "/#organisation"}}
                                   for p in TEAM]}],
    }, body, trail=[("/about/", "About"), ("/about/team/", "Meet the team")],
        active=None), priority="0.7", changefreq="monthly")

    for p in TEAM:
        wrote = [a for a in LEARN_ARTICLES if a["author"] == p["slug"]]
        reviewed = [a for a in LEARN_ARTICLES if a["reviewer"] == p["slug"]]
        wl = "".join('<li><a href="/learn/%s/%s/">%s</a></li>'
                     % (a["cluster"], a["slug"], e(a["title"])) for a in wrote)
        rl = "".join('<li><a href="/learn/%s/%s/">%s</a></li>'
                     % (a["cluster"], a["slug"], e(a["title"])) for a in reviewed)
        pbody = sec(f"""
<div style="display:grid;grid-template-columns:.8fr 1.6fr;gap:44px;align-items:start" class="psplit">
  <div>
    <div class="person-img" aria-hidden="true" style="font-size:3.4rem">{e(p['initials'])}</div>
    <p class="small muted" style="margin-top:14px">{e(p['reg'])}<br>
      <a href="https://www.pharmacyregulation.org/registers" rel="noopener">Check this registration</a></p>
  </div>
  <div class="prose">
    <p class="eyebrow">{e(p['role'])}</p>
    <h1>{e(p['name'])}</h1>
    <p class="lead">{e(p['about'])}</p>
    <h2>Roles and responsibilities</h2>
    <p>{e(p['responsibilities'])}</p>
    <h2>Qualifications and membership</h2>
    <p>{e(p['quals'])}</p>
    <h2>Specialist interest</h2>
    <p>{e(p['interest'])}</p>
    <h2>Interests outside work</h2>
    <p>{e(p['interests'])}</p>
    {('<h2>Articles written</h2><ul>%s</ul>' % wl) if wl else ''}
    {('<h2>Articles clinically reviewed</h2><ul>%s</ul>' % rl) if rl else ''}
  </div>
</div>
<style>@media(max-width:800px){{.psplit{{grid-template-columns:1fr !important}}}}</style>
{cluster_box("More", [("/about/team/", "All clinicians"), ("/about/", "About the clinic"),
                      ("/treatments/", "Treatments"), ("/consultation/", "Start a consultation")])}
""")
        write("/about/team/%s/" % p["slug"], page({
            "title": fit_title(
                "%s, %s | SmartGP clinic" % (p["name"], p["role"].split(" and ")[0]),
                "%s, %s | SmartGP weight loss clinic" % (p["name"], p["role"].split(" and ")[0]),
                "%s | %s at SmartGP" % (p["name"], p["role"]),
                "%s | SmartGP clinical team, UK" % p["name"],
                "%s | SmartGP clinical team" % p["name"]),
            "desc": fit_desc("%s is %s at SmartGP. Registration, responsibilities, "
                             "qualifications and the clinical content they have "
                             "written or reviewed."
                             % (p["name"], p["role"].lower())),
            "path": "/about/team/%s/" % p["slug"],
            "jsonld": [{"@context": "https://schema.org", "@type": "ProfilePage",
                        "url": ORIGIN + "/about/team/%s/" % p["slug"],
                        "mainEntity": {
                            "@type": "Person", "name": p["name"], "jobTitle": p["role"],
                            "description": p["about"],
                            "knowsAbout": [x.strip() for x in p["interest"].split(",")],
                            "worksFor": {"@id": ORIGIN + "/#organisation"},
                            "url": ORIGIN + "/about/team/%s/" % p["slug"]}}],
        }, pbody, trail=[("/about/", "About"), ("/about/team/", "Meet the team"),
                         ("/about/team/%s/" % p["slug"], p["name"])], active=None),
            priority="0.5", changefreq="yearly")


def build_testimonials():
    qs = "".join('<blockquote class="quote"><p>&ldquo;%s&rdquo;</p>'
                 '<footer>%s &middot; %s</footer></blockquote>' % (e(q), e(by), e(on))
                 for q, by, on in TESTIMONIALS)
    body = sec(f"""
<h1>Testimonials</h1>
<p class="lead">Feedback from patients about the service they received. Every
testimonial is moderated before publication.</p>
<div class="notice notice-flag" style="max-width:74ch;margin-top:24px">
  <h2>What we cannot publish</h2>
  <p style="margin:0">Testimonials are limited to the experience of using the
  service. Any review that names a prescription medicine or describes a weight-loss
  outcome is rejected, because prescription-only medicines cannot be advertised to
  the public.</p>
</div>
<h2 style="margin-top:36px">What patients say</h2>
<div class="grid g3" style="margin-top:20px">{qs}</div>
""")
    write("/about/testimonials/", page({
        "title": fit_title("What patients say about our service | SmartGP clinic"),
        "desc": "Moderated patient feedback on booking, consultation and delivery at "
                "SmartGP. Limited to service experience — we cannot publish outcome "
                "claims.",
        "path": "/about/testimonials/",
    }, body, trail=[("/about/", "About"), ("/about/testimonials/", "Testimonials")],
        active=None), priority="0.5", changefreq="monthly")


def build_careers():
    items = "".join(f"""<div class="li">
  <div class="li-main"><b>{e(t)}</b><span>{e(loc)}</span>
    <p class="small muted" style="margin:6px 0 0">{e(d)}</p></div>
  <a class="btn btn-ghost btn-sm" href="/contact/">Apply</a>
</div>""" for t, loc, d in CAREERS)
    body = sec(f"""
<h1>Careers at SmartGP</h1>
<p class="lead">We are building a clinic, not a storefront. If that appeals, get in touch.</p>
<h2 style="margin-top:32px">Current vacancies</h2>
<div class="list" style="margin-top:18px">{items}</div>
<p class="small muted" style="margin-top:18px">Applications are held for 6 months
after the recruitment decision and then deleted.</p>
""")
    write("/about/careers/", page({
        "title": fit_title("Careers at SmartGP | Clinical and pharmacy vacancies"),
        "desc": "Current vacancies at SmartGP and SmartRx Pharmacy — prescribers, "
                "dispensers and patient support. How to apply and how long we keep "
                "your application.",
        "path": "/about/careers/",
    }, body, trail=[("/about/", "About"), ("/about/careers/", "Careers")], active=None),
        priority="0.4", changefreq="monthly")


# ==========================================================================
# 7. CONTACT + LEGAL + 404
# ==========================================================================
def build_contact():
    body = sec(f"""
<div style="display:grid;grid-template-columns:1.2fr .8fr;gap:44px" class="csplit">
  <div>
    <h1>Contact the clinic</h1>
    <p class="lead">For anything that is not urgent. If your concern is urgent, call
    NHS 111. In an emergency, call 999.</p>

    {emergency_panel(2)}

    <form class="card" data-contact>
      <fieldset>
        <legend>Send us a message</legend>
        <div class="row2">
          <div class="field"><label for="cn">Your name <span class="req">*</span></label>
            <input id="cn" name="name" type="text" autocomplete="name" required></div>
          <div class="field"><label for="ce">Email <span class="req">*</span></label>
            <input id="ce" name="email" type="email" autocomplete="email" required></div>
        </div>
        <div class="field"><label for="ct">What is this about? <span class="req">*</span></label>
          <select id="ct" name="topic" required>
            <option value="">Please choose</option>
            <option>Booking an appointment</option><option>My order or delivery</option>
            <option>A side effect</option><option>Billing</option>
            <option>A complaint</option><option>Something else</option>
          </select></div>
        <div class="field"><label for="cm">Message <span class="req">*</span></label>
          <p class="hint" id="cm-hint">Please do not include clinical details you would rather discuss with a clinician.</p>
          <textarea id="cm" name="message" aria-describedby="cm-hint" required></textarea></div>
        <button class="btn btn-solid" type="submit">Send enquiry</button>
        <p class="small muted" style="margin-top:12px">Enquiries go to the clinic inbox
        and are answered within one working day.</p>
      </fieldset>
    </form>
  </div>
  <aside>
    <div class="card" style="margin-bottom:18px"><h2 style="font-family:var(--f-body);font-size:1rem;font-weight:700">Opening hours</h2>
      <p style="margin:0">Monday to Friday, 9:00 to 18:00<br>Closed on UK bank holidays<br>All times Europe/London.</p></div>
    <div class="card" style="margin-bottom:18px"><h2 style="font-family:var(--f-body);font-size:1rem;font-weight:700">Clinic details</h2>
      <address style="font-style:normal;margin:0">{e(BRAND['company'])}<br>{e(BRAND['office'])}<br>
      <a href="mailto:{e(BRAND['email'])}">{e(BRAND['email'])}</a></address></div>
    <div class="card"><h2 style="font-family:var(--f-body);font-size:1rem;font-weight:700">Complaints</h2>
      <p style="margin:0">We acknowledge within 3 working days.
      <a href="/legal/complaints/">Read the procedure</a>.</p></div>
  </aside>
</div>
<style>@media(max-width:900px){{.csplit{{grid-template-columns:1fr !important}}}}</style>
""")
    write("/contact/", page({
        "title": fit_title("Contact SmartGP | Clinic details and enquiries form"),
        "desc": "Contact the SmartGP clinic about bookings, orders, billing or "
                "complaints. Answered within one working day. For urgent advice call "
                "NHS 111.",
        "path": "/contact/",
        "jsonld": [{"@context": "https://schema.org", "@type": "ContactPage",
                    "url": ORIGIN + "/contact/",
                    "mainEntity": {"@id": ORIGIN + "/#organisation"}}],
    }, body, trail=[("/contact/", "Contact us")], active="/contact/"),
        priority="0.6", changefreq="yearly")


def build_legal():
    for slug, (title, blocks) in LEGAL.items():
        inner = "".join("<h2>%s</h2><p>%s</p>" % (e(h), e(t)) for h, t in blocks)
        extra = ""
        if slug == "cookies":
            extra = """<div class="card" style="margin-top:26px">
  <h2 style="font-family:var(--f-body);font-size:1rem;font-weight:700">Your current choice</h2>
  <p id="cookiestate">Loading your current preference&hellip;</p>
  <div class="btnrow">
    <button class="btn btn-ghost btn-sm" data-cookie="reject">Turn analytics off</button>
    <button class="btn btn-solid btn-sm" data-cookie="accept">Turn analytics on</button>
  </div>
</div>"""
        body = sec(f"""
<h1>{e(title)}</h1>
<div class="prose">{inner}{extra}</div>
<p class="small muted" style="margin-top:30px">Placeholder wording for the prototype.
Final text is drafted and approved by Josh Cocklin before launch.</p>
""")
        write("/legal/%s/" % slug, page({
            "title": fit_title(
                "%s | SmartGP online weight loss clinic UK" % title,
                "%s | SmartGP online weight loss clinic" % title,
                "%s | SmartGP weight loss clinic" % title,
                "%s | SmartGP" % title),
            "desc": "%s for SmartGP, the private online weight loss service operated "
                    "by %s in the United Kingdom." % (title, BRAND["company"]),
            "path": "/legal/%s/" % slug,
        }, body, trail=[("/legal/%s/" % slug, title)], active=None),
            priority="0.3", changefreq="yearly")


def build_404():
    body = sec("""
<h1>That page has moved</h1>
<p class="lead">The address you tried does not exist on this site. It may have been
renamed, or the link that sent you here may be out of date.</p>
<h2>Try one of these instead</h2>
<ul style="max-width:60ch">
  <li><a href="/treatments/">Weight loss treatments</a> — what we prescribe and who it suits</li>
  <li><a href="/pricing/">Pricing</a> — every strength and pack</li>
  <li><a href="/learn/">Learn</a> — clinician-written guides</li>
  <li><a href="/support/">Support</a> — the questions people ask most</li>
  <li><a href="/contact/">Contact us</a> — if you cannot find what you need</li>
</ul>
""")
    (OUT / "404.html").write_text(page({
        "title": "Page not found | SmartGP",
        "desc": "That page does not exist on the SmartGP site. Find treatments, "
                "pricing, guides and support here instead.",
        "path": "/404.html", "noindex": True,
    }, body, trail=None, active=None), encoding="utf-8")


# ==========================================================================
# 8. APP SHELLS — consultation, account, admin (noindex)
# ==========================================================================
def app_shell(path, title, desc, mount, extra_head=""):
    body = ('<div id="app" data-mount="%s"><div class="wrap" style="padding:60px 0">'
            '<h1>%s</h1><p class="lead">Loading&hellip;</p>'
            '<noscript><p class="notice notice-flag">This part of SmartGP needs '
            'JavaScript. Everything you need before booking &mdash; treatments, '
            'prices, guides and answers &mdash; works without it: '
            '<a href="/treatments/">see the treatments</a>.</p></noscript>'
            '</div></div>' % (mount, e(title.split(" | ")[0])))
    out = (head({"title": title, "desc": desc, "path": path, "noindex": True})
           + header(None)
           + '<main id="main">' + body + "</main>"
           + footer().replace('<script src="/assets/js/site.js" defer></script>',
                              '<script src="/assets/js/site.js" defer></script>\n'
                              '<script src="/assets/js/app.js" defer></script>'))
    write(path, out)


def build_app_shells():
    app_shell("/consultation/", "Start your consultation | SmartGP",
              "Begin your SmartGP weight loss consultation. Around eight minutes, "
              "then book a video appointment.", "journey")
    app_shell("/account/", "Your account | SmartGP",
              "Sign in to manage appointments, request a repeat and report a side "
              "effect.", "account")
    app_shell("/admin/", "SmartGP admin", "Back office.", "admin")


# ==========================================================================
# 9. robots.txt + sitemap.xml
# ==========================================================================
def build_app_data():
    """The app reads the same catalogue and question set the pages are built
    from, so a price or a question can never differ between the two."""
    data = {
        "services": [{
            "id": s["id"], "kind": s["kind"], "name": s["name"], "short": s["short"],
            "strapline": s["strapline"], "blurb": s["blurb"],
            "priceFrom": s["price_from"], "published": s["published"],
            "strengths": s["strengths"], "info": s["info"],
            "cautions": s["cautions"], "module": s["module"],
            "approval": s["approval"],
        } for s in SERVICES],
        "common": COMMON,
        "checkin": CHECKIN,
        "emergency": EMERGENCY,
        "booking": BOOKING,
        "team": [{"name": p["name"], "role": p["role"]} for p in TEAM],
    }
    (OUT / "assets" / "js" / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def build_meta_files():
    urls = "".join(
        "\n  <url><loc>%s%s</loc><lastmod>2026-08-19</lastmod>"
        "<changefreq>%s</changefreq><priority>%s</priority></url>"
        % (ORIGIN, p, cf, pr) for p, pr, cf in sorted(INDEXABLE, key=lambda x: -float(x[1])))
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s\n</urlset>\n' % urls,
        encoding="utf-8")

    (OUT / "robots.txt").write_text(f"""# SmartGP
User-agent: *
Allow: /

# Authenticated and in-progress clinical journeys. These hold personal health
# information and have no value in search. They are noindex at page level, which
# is what actually removes them; these rules only save crawl budget.
Disallow: /consultation/
Disallow: /account/
Disallow: /admin/

# Session and tracking parameters that would otherwise duplicate real pages.
Disallow: /*?session=
Disallow: /*?utm_

Sitemap: {ORIGIN}/sitemap.xml
""", encoding="utf-8")


# ==========================================================================
def main():
    for p in list(OUT.glob("*")):
        if p.name == "assets":
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()

    build_home()
    build_treatments()
    build_pricing()
    build_learn()
    build_support()
    build_about()
    build_contact()
    build_legal()
    build_404()
    build_app_shells()
    build_app_data()
    build_meta_files()

    pages = len(list(OUT.rglob("index.html")))
    print("Built %d pages (%d indexable) into %s" % (pages, len(INDEXABLE), OUT))


if __name__ == "__main__":
    main()
