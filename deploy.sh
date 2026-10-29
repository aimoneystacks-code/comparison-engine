#!/usr/bin/env bash
# Build and deploy to Cloudflare Pages.
# One-time: npm i -g wrangler && wrangler login
# Then: ./deploy.sh my-comparison-site
set -euo pipefail
FEED="${2:-feeds/sample.json}"
PROJECT="${1:?usage: ./deploy.sh <cloudflare-project-name> [feed.json]}"
python3 generate.py "$FEED"
npx wrangler pages deploy dist --project-name="$PROJECT"
