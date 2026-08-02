# DuckDuckGo Lite HTML Search Fallback

> When Composio search, Google, Bing, or other search engines are CAPTCHA-blocked
> from automated curl, DuckDuckGo Lite returns clean, parseable HTML with no blocks.

## How It Works

DuckDuckGo offers a stripped-down search interface at `lite.duckduckgo.com/lite`
that returns minimal HTML — no JavaScript, no tracking payloads, no CAPTCHA.
It's designed for low-bandwidth browsers, which makes it ideal for terminal-based
research.

## Pattern

### Step 1: Search

```bash
curl -sL "https://lite.duckduckgo.com/lite/?q=YOUR+SEARCH+QUERY+HERE" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -o /tmp/ddg-results.html
```

**Important:** Pass a realistic `User-Agent` header. DDG Lite works without one
but returns better results with a browser UA.

### Step 2: Extract Result URLs

```bash
grep -oP '(?<=<a rel="nofollow" href=")[^"]+' /tmp/ddg-results.html \
  | head -10
```

This extracts the redirect URLs from DDG's result links. Each URL looks like:
`//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2F...`

### Step 3: Decode and Fetch Individual Pages

The URLs are DuckDuckGo redirect URLs. Extract the actual target with:

```bash
# From the DDG redirect URL, decode the uddg parameter
python3 -c "
import urllib.parse, sys
lines = sys.stdin.read().strip().split('\n')
for url in lines:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if 'uddg' in qs:
        print(urllib.parse.unquote(qs['uddg'][0]))
" < /tmp/ddg-urls.txt > /tmp/actual-urls.txt
```

Then fetch each page:

```bash
while IFS= read -r url; do
  echo "=== $url ==="
  curl -sL "$url" -H "User-Agent: Mozilla/5.0" \
    | sed 's/<[^>]*>//g' \
    | sed '/^$/d' \
    | tr -s ' ' \
    | head -200
  echo
done < /tmp/actual-urls.txt
```

### Step 4: Extract Readable Content (Heavy HTML Pages)

For pages with lots of script/style noise, use a more thorough strip:

```bash
# Single-pipe version for quick reads
curl -sL "URL" -H "User-Agent: Mozilla/5.0" \
  | sed 's/<[^>]*>//g' \
  | sed '/^$/d' \
  | tr -s ' ' \
  | grep -v '^\s*$' \
  | head -200
```

For pages that still have CSS/JS noise, pre-filter with:

```bash
curl -sL "URL" -H "User-Agent: Mozilla/5.0" -o /tmp/page.html
# Remove script and style blocks
sed -i '/<script/,/<\/script>/d; /<style/,/<\/style>/d' /tmp/page.html
# Then strip remaining tags
sed 's/<[^>]*>//g' /tmp/page.html | sed '/^$/d' | head -200
```

## When to Use

- Composio search tools are unavailable (returning "Unknown tool" errors)
- Google/DuckDuckGo/Bing full sites return CAPTCHA or block automated access
- You need to find specific articles but don't have URLs pre-loaded
- Fetching known-good source URLs (Buffer, Hootsuite, Later — verified curl-friendly)

## When NOT to Use

- You already have the specific URL → fetch it directly (skip the search step)
- The topic is a documented Wikipedia subject → use Wikipedia API instead (cleaner JSON)
- You need real-time or JS-dependent content → this won't work (use browser instead)

## Verified Working (July 2026)

- DuckDuckGo Lite: always returns results, no rate limiting observed
- Buffer library (`buffer.com/resources/...`): clean HTML extraction
- Mittal Technologies (`mittaltechnologies.com/...`): clean extraction with sed
- Hootsuite blog: returns readable text through curl

## Pitfalls

- ❌ Some sites (Forbes, Adobe) serve JS-dependent content that sed stripping can't recover — skip those and find alternative sources
- ❌ DDG Lite results are less complete than full DuckDuckGo — you may get 8-10 results instead of 20+
- ❌ The `pipeto-interpreter blocking` security rule still applies — write to temp files, don't pipe into python3/bash directly
- ❌ Some CDNs block non-browser User-Agents even with a Mozilla UA — try adding `--header "Accept: text/html"` as a fallback
