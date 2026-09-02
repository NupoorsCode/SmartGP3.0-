# SmartGP — website build

Arranged the way a live site is arranged: real directory URLs, one HTML file per
page, generated at build time. The colour scheme, typography and the hero
(“Say hello to a new you”) are unchanged. The finalised logo is now used
throughout.

## Run it

```bash
python3 src/build.py          # regenerate site/
cd site && python3 -m http.server 8000
```

Open <http://localhost:8000>. **It must be served over HTTP**, not opened from
disk — the consultation app fetches its catalogue over the network, and
root-relative URLs (`/treatments/`) only resolve from a server root.

The old `build.py`, which inlined everything into one file, has been removed.
It existed because the prototype *was* one file; that is the thing this change
undoes. `preview-homepage.html` is generated for emailing a look at the design.

## Why it is no longer a single-page app

The previous build was one HTML file with hash routes (`#/treatments`). Search
engines cannot index that: there is one URL, one title, one description, and no
content in the initial response. Every SEO fix below depends on undoing it.

Public pages are now static HTML with all content in the first response and no
JavaScript dependency. The consultation, account and admin areas remain a JS app
— they sit behind a login, hold health data, and are `noindex`, so there is
nothing for a crawler to gain.

## Structure

```
src/
  content.py            content model — the single source of truth
  build.py              templates, schema, breadcrumbs, page generation
site/
  index.html                                    /
  treatments/index.html                         /treatments/
  treatments/{slug}/index.html                  5 treatment pages
  pricing/index.html
  learn/index.html                              hub
  learn/{cluster}/index.html                    3 topic hubs
  learn/{cluster}/{article}/index.html          7 articles
  support/index.html                            FAQ + FAQPage schema
  support/patient-resources/index.html
  about/index.html
  about/team/index.html
  about/team/{slug}/index.html                  3 clinician profiles
  about/testimonials/index.html
  about/careers/index.html
  contact/index.html
  legal/{terms,privacy,cookies,complaints,accessibility}/index.html
  consultation/index.html                       app shell, noindex
  account/index.html                            app shell, noindex
  admin/index.html                              app shell, noindex, unlinked
  404.html
  robots.txt
  sitemap.xml                                   34 indexable URLs
  assets/css/styles.css
  assets/js/site.js                             4.6 KB, public pages
  assets/js/app.js                              app areas only
  assets/js/data.json                           generated from content.py
  assets/img/smartgp-logo-{480,960}.png
```

## What changed, and why

### Flat architecture
Every page is reachable within three clicks of the homepage. The deepest URL is
an article at `/learn/{cluster}/{article}/`, which is Home → Learn → topic →
article.

### Simple URLs
Hash routes are gone. `#/treatment/mounjaro` became
`/treatments/mounjaro-tirzepatide/` — short, lower case, hyphenated,
keyword-bearing, and stable enough not to need redirecting later. Every page
carries a self-referencing canonical.

### Internal links and topic clusters
Three clusters — GLP-1 medicines, eating and moving well, side effects. Each has
a hub page. Every article links up to its hub, across to its siblings, and out
to the treatment it concerns; every treatment page links back to the articles
about it. Anchor text is descriptive throughout — no “click here” or “read more”
anywhere. A "Related reading" block at the foot of each substantial page carries
those links rather than leaving them to chance. Checked: 1,902 internal links,
zero broken, zero orphan pages except `/admin/`, which is unlinked on purpose.

### Breadcrumbs
On every page below the homepage, as a real `<nav aria-label="Breadcrumb">` with
an ordered list. The visible trail and the `BreadcrumbList` structured data are
generated from the same Python list, so they cannot drift apart.

### Heading hierarchy
Exactly one `<h1>` per page, no skipped levels — both checked programmatically
on every build. That check caught four real problems during this work, including
footer headings that jumped `h1` → `h3` on the app shells.

### E-E-A-T
- Every article names its **author** and the **clinician who reviewed it**, with
  published, last-reviewed and next-review dates, and links to both profiles.
- Clinician profiles carry role, registration number, responsibilities,
  qualifications, specialist interest, and the articles they wrote or reviewed —
  a two-way author↔content link.
- `Person` schema on profiles, `author` and `reviewedBy` on articles,
  `lastReviewed` and `reviewedBy` on treatment pages.
- Regulatory footer on every page: registered company and number, office, GPhC
  premises number with a link to the public register, Superintendent Pharmacist,
  prescriber regulators, CQC position, complaints route.
- Sources listed on every article.
- Deliberately **no** `Review` or `AggregateRating` markup. There are no verified
  reviews yet, and inventing rating markup is both a manual-action risk and an
  advertising-rules problem for a healthcare provider.

### Crawlability
- All content server-rendered; nothing needs JavaScript to be read.
- FAQ answers ship inside `<details>` and are readable with JS off; the search
  box only filters them.
- Mobile navigation is visible by default and *hidden* by JS — backwards from the
  usual pattern, so navigation survives with JS disabled.
- `robots.txt` disallows the three app areas to save crawl budget, with a comment
  noting that the page-level `noindex` is what actually removes them.
- `sitemap.xml` lists only the 34 indexable URLs.

### Structured data
64 JSON-LD blocks, all validated as parseable: `MedicalBusiness` + `Pharmacy`,
`WebSite`, `Drug` with one `Offer` per strength, `MedicalWebPage`, `FAQPage`,
`BreadcrumbList`, `Person`, `ProfilePage`, `CollectionPage`, `AboutPage`,
`ContactPage`.

### Core Web Vitals
- The logo has explicit `width`/`height` and a `srcset`, so it reserves its space
  and cannot shift the header (CLS).
- Public pages load 4.6 KB of deferred JavaScript. The 76 KB app bundle loads
  only on the three noindex app pages.
- No layout-shifting injected content; the cookie bar overlays rather than pushes.
- Fonts still come from Google Fonts with `display=swap`, trimmed to the weights
  actually used. **Self-hosting these is the single biggest remaining
  performance win** — see below.

### Accessibility
Skip link, visible focus ring never removed, `aria-current="page"` on the active
nav item and breadcrumb, labels on every input, `aria-describedby` for hints,
radio and checkbox groups in `<fieldset>`/`<legend>`, 44 px minimum tap targets,
`prefers-reduced-motion` respected, table `<caption>` and `scope` attributes.

### Prices cannot drift
Prices, strengths and availability are defined once in `src/content.py`. The
treatment pages, the pricing page, the comparison table, the `Offer` schema and
the consultation app all read from that one definition — the app via a generated
`data.json`. There is no second copy to forget to update.

## Still to do

1. **Self-host the three fonts.** They are currently two extra connections and a
   render-blocking stylesheet on every page. I could not download them here
   (`fonts.googleapis.com` is outside this environment's network allowlist).
2. **Run PageSpeed Insights on a deployed copy.** There is no browser in this
   environment, so the layout is reasoned rather than seen and there are no
   Lighthouse numbers — the decisions above are sound, not measured.
3. **Add real photography** for clinicians and treatments, as WebP/AVIF with
   `srcset`, explicit dimensions, `loading="lazy"` below the fold and alt text
   under 125 characters. The slots are marked; the initials placeholders are CSS,
   not images.
4. **301-redirect map** from any existing SmartRx or SmartGP URL before launch.
5. **Replace every bracketed placeholder** — company number, GPhC premises
   number, Vinesh's surname, registration numbers, CQC provider ID, phone.
6. **Confirm Wegovy oral.** Appendix D of the BRD lists an oral Wegovy at 1.5 mg
   and 4 mg. That branding does not match the licensed UK product I know of, and
   the page carries a visible flag saying so. Needs Rachel Wood to confirm before
   it is published.
7. **Server-side rendering in the real build.** Q36 commits to Laravel + Inertia +
   React, which renders client-side by default. If the public pages ship that way
   they undo everything above. Serve these pages statically or with SSR, and keep
   Inertia for the authenticated areas — which is exactly how this is arranged.

## Checks run on every build

```
38 files · 64 JSON-LD blocks · 0 structural problems · 0 metadata out of range
1,902 internal links · 0 broken · 0 unintended orphans
```

Titles are all 50–60 characters and descriptions all ≤160, enforced by
`fit_title()` and `fit_desc()` in `build.py` rather than by hand.
