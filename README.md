# Comparison Engine

A working static comparison-site generator. Feed it product data, get a
deployable site with affiliate links, structured data, and a price table.

```
generate.py            # the whole engine, stdlib only
feeds/sample.json      # product feed (swap this for your niche)
config/affiliates.json # your program IDs (empty = links pass through direct)
dist/                  # build output, deploy this folder
```

```bash
python3 generate.py feeds/sample.json
```

Output: `dist/index.html`, one page per product in `dist/p/`, plus
`sitemap.xml` and `robots.txt`. Deploy the folder anywhere static
(Cloudflare Pages, Netlify, S3). No server, no database, ~$0/mo.

---

## Read this before you scale it

Four things in the original plan do not work the way they sound. This matters
more than the code, because each one can get an account terminated.

**1. Google is not a retailer with a commission program.**
There is no "Google affiliate." Google Shopping is where *buyers come from*,
not where you send them to earn. Your monetizable destinations are Amazon,
eBay, and Walmart. Treat Google as the traffic channel.

**2. Prices cannot be scraped.**
Amazon's Operating Agreement prohibits scraping and requires the Product
Advertising API for price display, with refresh rules. eBay has a licensed
Browse API. Walmart exposes product data through Impact once approved. Every
legitimate feed in this engine must come from those, or be entered by hand.
A scraper at scale is the fastest route to a banned account.

**3. Amazon will not pay you through PayPal.**
Each program pays on its own rails. Amazon Associates pays by direct deposit,
check, or gift card. eBay Partner Network pays via PayPal. Walmart through
Impact pays by bank or PayPal depending on your settings. "All commission to
my PayPal" is a per-program setting at signup, and one of the three can't
go there at all.

**4. Approval is the real gate, not the build.**
None of these programs approve a new site with no traffic. Amazon also requires
three qualifying sales within 180 days of approval to stay in. So the sequence
is: build one real site -> publish genuinely useful content -> apply -> get
approved -> then add the second and third program.

---

## Why "multiply and repeat" backfires

Mass-generating near-identical thin sites is explicitly what Google's spam
policy calls scaled content abuse, and Amazon prohibits the pattern in its own
terms. The outcome is deindexing and termination, not compounding income.

The version that actually scales: **one site per distinct buying intent**, each
with data you can't get from a generic template (your own testing, real spec
tables, price history you captured over time). Automation handles the boring,
safe part only: refresh prices, rebuild, redeploy. It does not invent content.

## Honest economics

Comparison traffic converts at roughly 1-3% to an outbound click, and outbound
clicks convert at maybe 2-5% to a sale. Electronics commissions sit at 3-4%.
So ~10k monthly visitors on a headphone site is on the order of $15-40/mo.

The money is in commission rate, not traffic: software, mattresses, home
services, and insurance pay 20-100x what consumer electronics does. Pick a
niche where the payout per sale is worth the same effort. One site in a
high-commission niche beats ten electronics sites.

## Operating order

1. Pick one niche you actually know something about. Real knowledge is the
   only durable advantage; it's the thing a template can't fake.
2. Fill `feeds/sample.json` with 15-40 products. Start by hand or from a
   licensed API. The schema is self-explanatory; copy an entry and edit it.
3. Run `python3 generate.py feeds/<your-feed>.json`. Open `dist/index.html`.
4. Deploy: `npx wrangler pages deploy dist --project-name=<name>`
   (or drag the folder into Netlify).
5. Apply to Amazon Associates, eBay Partner Network, and Walmart/Impact.
   Expect to be declined once or twice before approval. Fix and reapply.
6. Paste the approved IDs into `config/affiliates.json` and rebuild. Run
   `python3 generate.py` and confirm the "affiliate-tracked links" count is
   not zero.
7. Only now automate: a weekly cron that reruns the generator and redeploys.
   That step needs a deploy token, which you'd store as a secret.

Step 7 is the only true autopilot here, and it's genuinely worth having:
stale prices are the main reason these sites lose trust and rankings.
