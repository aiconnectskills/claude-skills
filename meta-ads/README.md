# Meta Ads Skill for Claude

A Claude Code / Cowork skill that lets you pull, analyze, manage, and create Meta ads (Facebook, Instagram, Messenger, Threads, Click-to-WhatsApp) via the Marketing API.

## What it does

- **Analyze** ad performance — impressions, CTR, CPC, ROAS, frequency, creative fatigue
- **Create** full campaigns from scratch — campaign, ad sets, creatives, ads
- **Manage** existing campaigns — pause/resume, update budgets, duplicate winners
- **Detect** anomalies and creative fatigue automatically
- **Rollback** failed campaign creations safely

## Setup

1. Copy `assets/env.template` to `.env` in the skill root
2. Follow the step-by-step guide in `references/setup.md` to get your Meta API credentials
3. Run `python scripts/auth_check.py` to verify your setup

## File structure

```
meta-ads-skill/
├── SKILL.md                    # Skill instructions for Claude
├── assets/
│   └── env.template            # Environment variable template
├── scripts/
│   ├── meta_client.py          # Core API client (security-hardened)
│   ├── auth_check.py           # Verify credentials
│   ├── list_accounts.py        # List ad accounts
│   ├── list_campaigns.py       # List campaigns
│   ├── fetch_insights.py       # Pull performance data
│   ├── create_campaign.py      # Create full campaigns
│   ├── pause_ad.py             # Pause/resume ads
│   ├── update_budget.py        # Change budgets
│   ├── duplicate_ad.py         # Duplicate winning ads
│   ├── anomaly_detect.py       # Detect performance anomalies
│   ├── creative_fatigue.py     # Detect creative fatigue
│   ├── exchange_token.py       # Refresh user tokens
│   └── rollback_creation.py    # Rollback failed creations
└── references/
    ├── setup.md                # Step-by-step setup guide
    ├── campaign-creation.md    # Campaign creation reference
    ├── write-actions.md        # Safety rules for write operations
    ├── insights-fields.md      # Available metrics and breakdowns
    ├── analysis-playbooks.md   # Analysis templates
    └── troubleshooting.md      # Common errors and fixes
```

## Security

- TLS verification enforced on all API calls
- Pagination URL validation prevents SSRF
- Tokens never logged or displayed (redacted to first 8 chars)
- All write operations require explicit user confirmation
- Campaign creation includes automatic rollback on failure

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)
- Meta developer app with Marketing API access
- Valid access token (System User or long-lived user token)

## License

MIT
