# My News Preferences

This file defines what types of news articles are relevant to me. The LLM uses this as context to filter articles.

## High Priority Topics

These topics are extremely relevant - I want to be notified about any articles covering these areas:

- **Local Technology Events**: Conferences, meetups, hackathons, tech community events
- **Local Government & Technology**: Smart city initiatives, digital services, tech policy
- **Cybersecurity Incidents**: Local data breaches, security advisories affecting my area
- **Open Source Projects**: Local developers releasing open source software, FOSS community news

## Medium Priority Topics

I'm interested in these topics but only if they have significant local impact or relevance:

- **Education & Schools**: University tech programs, coding bootcamps, STEM education
- **Business & Startups**: Local tech companies, startup funding, business closures/openings
- **Infrastructure**: Internet infrastructure, 5G rollout, broadband expansion
- **Environment & Sustainability**: Green tech initiatives, climate policy, environmental data
- **Health Technology**: Telemedicine, health apps, medical technology advancements

## Low Priority Topics

Only notify me if these are major stories with broad impact:

- **Arts & Culture**: Tech-art intersections, digital art, media production
- **Transportation**: Electric vehicles, public transit technology, traffic systems
- **Real Estate**: Smart home technology, housing development with tech focus

## Topics to Ignore

Do NOT notify me about articles primarily focused on:

- Sports news (unless technology-related, e.g., esports)
- Celebrity gossip or entertainment
- Weather forecasts (unless extreme weather warnings)
- Crime reports (unless cybercrime or major security breaches)
- Political news (unless directly related to technology policy)
- Obituaries
- Local restaurant openings/closings (unless tech-focused venues)

## Specific Keywords

### High relevance keywords (boost score):
- Raspberry Pi
- Python programming
- AI/ML, artificial intelligence, machine learning
- Cybersecurity, InfoSec, penetration testing
- Linux, open source
- Privacy, encryption, data protection
- Cloud computing, AWS, Azure, GCP
- DevOps, CI/CD, automation
- Web development, APIs
- Blockchain (if local/technical, not just crypto prices)

### Negative keywords (reduce score):
- Casino, gambling
- Horoscope
- Recipe
- Coupons, deals, sales (unless tech products)
- Traffic accident
- Wedding announcement

## Article Characteristics

### Prefer articles that are:
- **Actionable**: Provide information I can use or act upon
- **Local**: Focus on my city/region/country
- **Technical**: Include technical details, not just surface-level coverage
- **Recent**: Published within the last 24 hours
- **Factual**: News reporting rather than opinion pieces (unless expert technical analysis)

### Avoid articles that are:
- **Clickbait**: Sensational headlines without substance
- **Duplicates**: Same story from multiple sources (keep the most detailed version)
- **Press releases**: Pure advertising or promotional content
- **Speculative**: Rumors or unconfirmed information

## Context About Me

I'm a software developer interested in:
- Self-hosting services on Raspberry Pi
- Home automation and IoT projects
- Privacy-focused technology
- Local tech community and learning opportunities
- Programming in Python, JavaScript, and Rust
- Running local LLMs and AI experiments

I live in [YOUR CITY/REGION] and want to stay informed about local tech news that might affect me or present opportunities to learn, network, or contribute.

## Scoring Guidance for LLM

Use this scale when rating articles:

- **10**: Directly relevant to my high-priority topics, actionable, local
- **8-9**: High-priority topic or very relevant medium-priority topic
- **6-7**: Medium-priority topic with good local relevance
- **4-5**: Low-priority topic or medium-priority with weak local connection
- **2-3**: Marginally relevant or contains negative keywords
- **1**: Should be ignored based on ignore list

When in doubt, prefer false negatives (miss an article) over false positives (notify me about irrelevant articles).
