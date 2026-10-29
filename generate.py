#!/usr/bin/env python3
"""
Static comparison-site generator.

Feed (JSON) + affiliate IDs (JSON) -> a deployable static site in dist/.
No dependencies, no framework, no build step beyond this file.

Usage:  python3 generate.py feeds/sample.json
"""
import json
import sys
import shutil
import html
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse, parse_qsl, urlunparse

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

RETAILERS = {
    "amazon":  {"label": "Amazon",          "class": "amazon"},
    "ebay":    {"label": "eBay",            "class": "ebay"},
    "walmart": {"label": "Walmart",         "class": "walmart"},
    "google":  {"label": "Google Shopping", "class": "google"},
}


# --------------------------------------------------------------------------
# affiliate link construction
# --------------------------------------------------------------------------
def affiliate_url(offer, cfg):
    """Wrap a merchant URL in the right affiliate tracking format.

    Returns the plain URL if that program is not configured yet, so the site
    is always shippable before approval.
    """
    base = offer["url"]
    retailer = offer["retailer"]
    conf = cfg.get(retailer, {}) or {}
    kind = conf.get("type", "none")

    if kind == "param":
        pid = (conf.get("id") or "").strip()
        if not pid:
            return base
        parts = urlparse(base)
        query = dict(parse_qsl(parts.query))
        query[conf["param"]] = pid
        return urlunparse(parts._replace(query=urlencode(query)))

    if kind == "rover":  # eBay Partner Network
        campid = (conf.get("campaign_id") or "").strip()
        if not campid:
            return base
        pub = (conf.get("publisher_id") or "").strip()
        custom = (conf.get("custom_id_prefix") or "") + offer.get("_slug", "")
        return (
            "https://rover.ebay.com/rover/1/711-53200-19255-0/1"
            f"?ff3=4&pub={quote(pub)}&toolid=10001&campid={quote(campid)}"
            f"&customid={quote(custom)}&mpre={quote(base, safe='')}"
        )

    if kind == "impact":  # Walmart via Impact.com
        pub = (conf.get("publisher_id") or "").strip()
        if not pub:
            return base
        camp = (conf.get("campaign_id") or "").strip()
        ad = (conf.get("ad_id") or "").strip()
        return f"https://goto.walmart.com/c/{pub}/{camp}/{ad}?u={quote(base, safe='')}"

    return base  # type none, e.g. Google has no affiliate program


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def money(value):
    return "${:,.2f}".format(value)


def esc(text):
    return html.escape(str(text), quote=True)


def best_offer(product):
    in_stock = [o for o in product["offers"] if o.get("in_stock")]
    pool = in_stock or product["offers"]
    return min(pool, key=lambda o: o["price"])


def enrich(site, products, cfg):
    """Attach computed fields the templates need."""
    for p in products:
        p["slug"] = p["id"]
        for o in p["offers"]:
            o["_slug"] = p["id"]
            o["href"] = affiliate_url(o, cfg)
        b = best_offer(p)
        p["best"] = b
        p["high"] = max(o["price"] for o in p["offers"])
        p["spread"] = round(p["high"] - b["price"], 2)
    return products


# --------------------------------------------------------------------------
# templates
# --------------------------------------------------------------------------
CSS = """
:root{
  --ink:#14181f; --muted:#5f6b7a; --line:#e3e7ec; --bg:#ffffff; --surface:#f7f9fb;
  --accent:#0f6b4f; --accent-ink:#ffffff; --warn:#a8420b;
  --radius:10px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:0 20px}
header.site{border-bottom:1px solid var(--line);padding:18px 0}
header.site .wrap{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
header.site a.brand{font-weight:700;letter-spacing:-.01em;color:var(--ink);text-decoration:none}
header.site nav a{color:var(--muted);text-decoration:none;font-size:14px;margin-right:16px}
header.site nav a:hover{color:var(--ink)}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;letter-spacing:-.02em;margin:34px 0 10px}
p.lede{color:var(--muted);font-size:17px;margin:0 0 24px;max-width:62ch}
h2{font-size:20px;letter-spacing:-.01em;margin:38px 0 12px}
p,li{font-size:16px}
a{color:var(--accent)}
.disclosure{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:12px 14px;font-size:13px;color:var(--muted);margin:22px 0 30px}
table.cmp{width:100%;border-collapse:collapse;margin:18px 0 8px;font-size:15px}
table.cmp th,table.cmp td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}
table.cmp th{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
table.cmp tr.best td{background:var(--surface)}
.price{font-variant-numeric:tabular-nums;font-weight:600}
.save{color:var(--accent);font-weight:600;font-size:13px}
.oos{color:var(--muted);font-size:13px;text-decoration:line-through}
.btn{display:inline-block;padding:9px 15px;border-radius:8px;background:var(--accent);
  color:var(--accent-ink);text-decoration:none;font-size:14px;font-weight:600;
  border:1px solid transparent;white-space:nowrap}
.btn:hover{filter:brightness(1.08)}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--line)}
.btn.ghost:hover{background:var(--surface);filter:none}
.card{border:1px solid var(--line);border-radius:var(--radius);padding:20px;margin:16px 0;background:var(--bg)}
.card .top{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;flex-wrap:wrap}
.card h3{margin:0 0 4px;font-size:19px;letter-spacing:-.01em}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{color:var(--accent)}
.brandline{font-size:13px;color:var(--muted)}
.stars{font-size:13px;color:var(--muted);white-space:nowrap}
.pill{display:inline-block;font-size:12px;font-weight:600;padding:3px 9px;border-radius:999px;
  background:var(--surface);border:1px solid var(--line);color:var(--muted)}
.pill.win{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
dl.specs{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin:16px 0 0;font-size:14px}
dl.specs dt{color:var(--muted)}
dl.specs dd{margin:0}
footer.site{border-top:1px solid var(--line);margin-top:56px;padding:26px 0 60px;
  color:var(--muted);font-size:13px}
footer.site a{color:var(--muted)}
@media(max-width:620px){
  table.cmp{display:block;overflow-x:auto;white-space:nowrap}
  .card{padding:16px}
}
"""


def shell(site, body, depth=0, canonical=""):
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(canonical or site['title'])}</title>
<meta name="description" content="{esc(site['tagline'])}">
{f'<link rel="canonical" href="{esc(site["base_url"])}/{"p/" if depth else ""}">' if site.get('base_url') else ''}
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{prefix}index.html">{esc(site['title'])}</a>
  <nav><a href="{prefix}index.html">All models</a><a href="{prefix}index.html#table">Price table</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
  <p>{esc(site['disclosure'])}</p>
  <p>Prices captured {esc(site['updated'])}. We do not sell your data. <a href="#">How we rank</a></p>
</div></footer>
</body>
</html>
"""


def jsonld(site, products):
    items = []
    for i, p in enumerate(products, start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Product",
                "name": p["name"],
                "brand": {"@type": "Brand", "name": p["brand"]},
                "description": p["summary"],
                "offers": [{
                    "@type": "Offer",
                    "price": f"{o['price']:.2f}",
                    "priceCurrency": "USD",
                    "availability": "https://schema.org/InStock" if o.get("in_stock") else "https://schema.org/OutOfStock",
                    "url": o["href"],
                    "seller": {"@type": "Organization", "name": RETAILERS[o["retailer"]]["label"]},
                } for o in p["offers"]],
            },
        })
    data = {"@context": "https://schema.org", "@type": "ItemList",
            "name": site["title"], "itemListElement": items}
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def offer_rows(product, note_prices=True):
    rows = []
    best = product["best"]
    for o in sorted(product["offers"], key=lambda x: (not x.get("in_stock"), x["price"])):
        label = RETAILERS[o["retailer"]]["label"]
        is_best = o is best
        price_cell = (
            f'<span class="{"price" if o.get("in_stock") else "oos"}">{money(o["price"])}</span>'
            if o.get("in_stock") else
            f'<span class="price oos">{money(o["price"])}</span> <span class="pill">Out of stock</span>'
        )
        note = f' <span class="brandline">{esc(o["note"])}</span>' if o.get("note") else ""
        action = (
            f'<a class="btn{" ghost" if not is_best else ""}" href="{esc(o["href"])}" '
            f'rel="nofollow sponsored noopener" target="_blank">View at {esc(label)}</a>'
            if o.get("in_stock") else
            f'<span class="brandline">Unavailable</span>'
        )
        rows.append(
            f'<tr class="{"best" if is_best else ""}">'
            f'<td><strong>{esc(label)}</strong>{note}</td>'
            f'<td>{price_cell}</td>'
            f'<td>{esc(o.get("shipping","-"))}</td>'
            f'<td>{action}</td></tr>'
        )
    return "\n".join(rows)


def index_body(site, products):
    rows = []
    for p in products:
        b = p["best"]
        save = f'<span class="save">Save {money(p["spread"])}</span>' if p["spread"] > 0.5 else ""
        rows.append(
            f'<tr class="best"><td><a href="p/{esc(p["slug"])}.html"><strong>{esc(p["name"])}</strong></a>'
            f'<div class="brandline">{esc(p["brand"])}</div></td>'
            f'<td><span class="price">{money(b["price"])}</span> <div class="brandline">'
            f'{esc(RETAILERS[b["retailer"]]["label"])}</div></td>'
            f'<td>{save}</td>'
            f'<td><a class="btn" href="p/{esc(p["slug"])}.html">Compare</a></td></tr>'
        )

    cards = []
    for p in products:
        specs = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in p["specs"].items())
        cards.append(f"""
<article class="card">
  <div class="top">
    <div>
      <h3><a href="p/{esc(p['slug'])}.html">{esc(p['name'])}</a></h3>
      <div class="brandline">{esc(p['brand'])}</div>
    </div>
    <div style="text-align:right">
      <div class="pill win">Best {money(p['best']['price'])} at {esc(RETAILERS[p['best']['retailer']]['label'])}</div>
      <div class="stars">&#9733; {p['rating']} / 5</div>
    </div>
  </div>
  <p>{esc(p['summary'])}</p>
  <dl class="specs">{specs}</dl>
  <p style="margin-top:18px">
    <a class="btn" href="p/{esc(p['slug'])}.html">All {len(p['offers'])} prices</a>
  </p>
</article>""")

    return f"""
<h1>{esc(site['title'])}</h1>
<p class="lede">{esc(site['tagline'])}</p>
<p class="disclosure">{esc(site['disclosure'])}</p>

<h2 id="table">Price comparison</h2>
<table class="cmp">
  <thead><tr><th>Model</th><th>Lowest price</th><th>You save</th><th></th></tr></thead>
  <tbody>
  {''.join(rows)}
  </tbody>
</table>

<h2>The shortlist</h2>
{''.join(cards)}
{jsonld(site, products)}
"""


def product_body(site, products, p):
    specs = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in p["specs"].items())
    related = [x for x in products if x["id"] != p["id"]][:3]
    rel = "".join(
        f'<li><a href="{esc(x["slug"])}.html">{esc(x["name"])}</a> '
        f'&mdash; from {money(x["best"]["price"])}</li>'
        for x in related
    )
    return f"""
<p class="brandline" style="margin:28px 0 0"><a href="../index.html">All models</a> / {esc(p['brand'])}</p>
<h1>{esc(p['name'])}</h1>
<div class="stars">&#9733; {p['rating']} / 5 &nbsp;&middot;&nbsp; best price {money(p['best']['price'])}</div>
<p class="lede" style="margin-top:14px">{esc(p['summary'])}</p>

<h2>Where to buy</h2>
<table class="cmp">
  <thead><tr><th>Retailer</th><th>Price</th><th>Shipping</th><th></th></tr></thead>
  <tbody>
  {offer_rows(p)}
  </tbody>
</table>
<p class="disclosure">{esc(site['disclosure'])}</p>

<h2>Specifications</h2>
<dl class="specs">{specs}</dl>

<h2>Also consider</h2>
<ul>{rel}</ul>
"""


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def main():
    feed_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "feeds" / "sample.json"
    feed = json.loads(feed_path.read_text())
    site = feed["site"]
    products = enrich(site, feed["products"], json.loads((ROOT / "config" / "affiliates.json").read_text()))

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "p").mkdir(parents=True)

    (DIST / "index.html").write_text(shell(site, index_body(site, products)))
    for p in products:
        (DIST / "p" / f"{p['slug']}.html").write_text(
            shell(site, product_body(site, products, p), depth=1, canonical=p["name"])
        )
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f'  <url><loc>/p/{p["slug"]}.html</loc></url>\n' for p in products)
        + "</urlset>\n"
    )

    linked = sum(1 for p in products for o in p["offers"] if "tag=" in o["href"]
                 or "rover.ebay.com" in o["href"] or "goto.walmart.com" in o["href"])
    total = sum(len(p["offers"]) for p in products)
    print(f"built {len(products)} products, {total} offers -> {DIST}")
    print(f"affiliate-tracked links: {linked}/{total}")


if __name__ == "__main__":
    main()
