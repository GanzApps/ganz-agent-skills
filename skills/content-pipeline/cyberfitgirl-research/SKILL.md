---
name: "cyberfitgirl-research"
description: "Research Agent for CyberFitGirl — finds fitness/health trends, keywords, competitors, and content opportunities for AI-generated image packs."
category: marketing-research
risk: safe
---

# CyberFitGirl Research Agent 🔍

Finds trends, keywords, competitors, and content opportunities for the CyberFitGirl AI image pack business.

## What It Does

1. **Trend Discovery** — What's hot in fitness, health, wellness, AI art
2. **Keyword Research** — What people search for on Etsy, Gumroad, Pinterest
3. **Competitor Tracking** — Who's selling what, at what price, how popular
4. **Content Opportunities** — Gaps to exploit, niches to own

## Commands

| Command | Description |
|---------|-------------|
| `!research now` | Run full research cycle immediately |
| `!research trends` | Find current trending topics only |
| `!research keywords <topic>` | Research keywords for a topic |
| `!research competitors` | Analyze competitor landscape |
| `!research report` | Generate full research report |

## Research Sources

### Trend Sources
- Google Trends (web search)
- Pinterest Trends
- TikTok Creative Center
- Etsy trending searches
- Reddit r/fitness, r/xxfitness, r/progresspics
- Instagram hashtags

### Competitor Sources
- Etsy search: "fitness planner", "workout tracker", "gym motivation"
- Gumroad discover
- Pinterest search
- Instagram accounts selling digital products

### Keyword Tools
- Web search for "best selling digital products fitness 2026"
- Etsy search suggestions
- Pinterest search suggestions
- Google autocomplete

## Output Format

### Trend Report
```
# Trend Report — [Date]

## 🔥 Hot Trends (This Week)
1. [Trend name] — [Why it's hot] — [Opportunity score 1-10]
2. ...

## 📈 Rising Trends (Watch List)
1. [Trend] — [Growth signal] — [Action]

## 💡 Content Opportunities
- [Specific pack idea] — [Target platform] — [Estimated demand]
- ...

## 🎯 Recommended Actions
1. [Action] — [Priority] — [ETA]
```

### Competitor Snapshot
```
# Competitor Analysis — [Date]

## Top Competitors
| Seller | Platform | Product | Price | Est. Sales | Strength | Weakness |
|--------|----------|---------|-------|------------|----------|----------|
| ... | ... | ... | ... | ... | ... | ... |

## Pricing Benchmarks
- Low: $X
- Mid: $X
- Premium: $X

## Gaps Found
- [Gap] — [Opportunity]
```

### Keyword List
```
# Keywords — [Topic]

## High Volume (Broad)
- keyword (volume: X, competition: high/mid/low)

## Long Tail (Specific)
- keyword (volume: X, competition: high/mid/low)

## Trending Now
- keyword (trend: +X%, source)
```

## Daily Automation

### 8 AM Report (Cron)
Runs automatically every day at 8 AM:
1. Check trending fitness/wellness topics
2. Check competitor activity
3. Generate brief report
4. Post to #cyberfitgirl channel
5. Flag high-priority opportunities for approval

## Implementation

### Files
- `research/trends.md` — Latest trend findings
- `research/competitors.md` — Competitor tracking
- `research/keywords.md` — Keyword database
- `research/reports/` — Daily/weekly reports

### Tools Used
- `web_search` — Trend and competitor research
- `web_fetch` — Deep dive on specific pages
- `message` — Post reports to Discord
- `cron` — Schedule daily reports

## Quality Rules

- Every claim needs a source
- Every trend needs evidence (search volume, social proof, or sales data)
- Every competitor claim needs a URL
- Flag uncertainty clearly
- Prioritize actionable insights over interesting facts
