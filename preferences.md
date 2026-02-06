# My News Preferences

This file defines what types of news articles are relevant to me. The LLM uses this as context to filter articles.

## High Priority Topics

These topics are extremely relevant - I want to be notified about any articles covering these areas:

### Technology & Digital
- **Local Technology Events**: Conferences, meetups, hackathons, tech community events
- **Cybersecurity**: Data breaches, security advisories, malware, hacking incidents
- **Local Tech Development**: New apps, services, digital infrastructure, smart city initiatives
- **Internet & Connectivity**: Broadband, 5G, network outages, ISP news
- **Open Source**: Local developers releasing FOSS, open source community news

### Health & Medical
- **Disease Outbreaks**: COVID-19 cases rising, dengue fever, flu outbreaks, epidemics
- **Public Health Alerts**: Vaccination campaigns, health warnings, contamination alerts
- **Healthcare System**: Hospital capacity, healthcare access, medical supply issues
- **Preventive Health**: Health screenings, disease prevention programs

### Microeconomy (Everyday Economics)
- **Cost of Living**: Price increases/decreases (food, gas, utilities, rent)
- **Wages & Employment**: Minimum wage changes, job market, unemployment, hiring freezes
- **Consumer Impact**: Inflation affecting households, subsidy programs, financial assistance
- **Local Business**: Store closures/openings that affect daily life, service disruptions
- **Banking & Finance for Regular People**: Account fees, credit access, payment systems

### Extreme Weather
- **Severe Weather Events**: Major storms, flooding, extreme heat waves, cold snaps
- **Weather Emergencies**: Emergency declarations, evacuation orders, weather warnings

## Medium Priority Topics

I'm interested in these topics if they have significant local impact:

### Technology (Medium Impact)
- **Education Technology**: School programs, coding bootcamps, online learning platforms
- **Tech Business**: Local startups, tech company expansions/closures, funding rounds
- **Government Digital Services**: Online services, digital ID, e-government initiatives

### Health (Medium Impact)
- **Healthcare Technology**: Telemedicine, health apps, medical devices
- **Medical Research**: Local clinical trials, research findings with practical impact
- **Mental Health**: Mental health services, support programs

### Economy (Medium Impact)
- **Public Services**: Transportation fare changes, utility rate changes
- **Benefits & Assistance**: Social programs, subsidies, government assistance
- **Consumer Rights**: Regulatory changes affecting consumers, recalls

## Low Priority Topics

Only notify me if these are major stories with broad impact:

- **Regular Weather**: Normal forecasts, seasonal weather (unless extreme)
- **Transportation**: Public transit updates, traffic systems (unless major disruption)
- **Infrastructure**: Road work, construction projects (unless major impact)
- **Education**: School system news (unless directly affecting families)
- **Environment**: Environmental initiatives (unless immediate health impact)

## Topics to Ignore

Do NOT notify me about articles primarily focused on:

- **Sports** (unless technology-related, e.g., esports)
- **Celebrity gossip, entertainment, game shows**
- **Political campaigns and partisan politics** (unless direct policy impact on daily life)
- **Crime reports** (unless cybercrime, major security breach, or public safety alert)
- **Obituaries and funerals**
- **Human interest stories** without practical relevance
- **Restaurant/bar openings** (unless major chain or food security issue)
- **Traffic accidents** (unless major highway closure)
- **Stock market news** (I care about microeconomy, not Wall Street)
- **Crypto prices and trading** (not interested in speculation)
- **Arts and culture events** (galleries, museums, concerts)
- **Real estate market trends** (unless affecting rental prices significantly)

## Specific Keywords

### High relevance keywords (boost score):

**Technology:**
- Python, JavaScript, programming, software development
- AI/ML, artificial intelligence, machine learning
- Cybersecurity, InfoSec, hacking, malware, ransomware
- Linux, open source, FOSS
- Cloud computing, DevOps, automation
- Privacy, encryption, data protection
- Internet outage, network issues

**Health:**
- COVID, coronavirus, dengue, flu outbreak
- Vaccination, vaccine, immunization
- Disease outbreak, epidemic, contagion
- Hospital emergency, health alert
- Contamination, food safety

**Economy:**
- Price increase, inflation, cost of living
- Minimum wage, salary, employment
- Subsidy, financial aid, assistance program
- Utility rates, gas prices, rent increase
- Layoffs, hiring, job market

**Weather:**
- Storm warning, heat wave, extreme weather
- Flooding, evacuation, weather emergency
- Temperature record, severe weather

### Negative keywords (reduce score):
- Casino, gambling, lottery
- Horoscope, astrology
- Recipe, cooking (unless food safety)
- Wedding, engagement
- Fashion, makeup
- Awards ceremony (unless tech/science)
- Celebrity, influencer, reality TV
- Stock market, trading, investment tips
- Cryptocurrency speculation

## Article Characteristics

### Prefer articles that are:
- **Actionable**: Information I can use (health warnings, price changes, service updates)
- **Local**: Focus on my city/region/country
- **Timely**: Recent developments, not old news
- **Factual**: News reporting, not opinion pieces
- **Impact-focused**: How does this affect regular people's daily lives?

### Avoid articles that are:
- **Clickbait**: Sensational headlines without substance
- **Speculative**: Rumors, unconfirmed information
- **Press releases**: Pure advertising
- **Macro-focused**: National politics, stock market, big business (unless it affects local economy)

## Scoring Guidance for LLM

Use this scale when rating articles:

- **10**: Urgent/critical (disease outbreak, severe weather warning, major security breach)
- **8-9**: High-priority topic with direct local impact (price increases, tech events, health alerts)
- **6-7**: Medium-priority topic with clear relevance (tech business, healthcare access, service changes)
- **4-5**: Low-priority topic or weak local connection (minor weather, infrastructure updates)
- **2-3**: Marginally relevant or contains negative keywords
- **1**: Should be ignored based on ignore list

## Examples

### ✅ RELEVANT Articles (Score 8-10):

**Technology:**
- "Local Hackathon Announced for March 15th" → **10** (Tech event)
- "Data Breach Exposes 5,000 Local Users' Information" → **10** (Cybersecurity)
- "City Launches New Digital Services App" → **9** (Tech development)
- "Internet Outage Affects Downtown Area" → **8** (Connectivity issue)

**Health:**
- "Dengue Cases Triple in Past Two Weeks" → **10** (Disease outbreak)
- "Health Ministry Issues COVID Alert for Region" → **10** (Health alert)
- "Free Vaccination Campaign Starts Monday" → **9** (Preventive health)
- "Hospital Emergency Room at Capacity" → **8** (Healthcare system)

**Microeconomy:**
- "Bread Prices Increase 15% Starting Next Month" → **9** (Cost of living)
- "Minimum Wage Raised to $X Effective March" → **9** (Wages)
- "Electricity Rates to Increase 20%" → **9** (Utility costs)
- "Major Supermarket Chain Closes 3 Local Stores" → **8** (Consumer impact)
- "Government Announces New Subsidy Program for Families" → **8** (Financial assistance)

**Weather:**
- "Heat Wave Warning: Temperatures Expected to Reach 40°C" → **10** (Extreme weather)
- "Storm Alert: Heavy Rainfall and Flooding Expected" → **10** (Weather emergency)

### ⚠️ BORDERLINE Articles (Score 4-6):

- "New Coworking Space Opens Downtown" → **5** (Tech-adjacent, minor impact)
- "School District Tests New Learning App" → **5** (Education tech)
- "City Announces New Bike Lane Construction" → **4** (Infrastructure, low impact)
- "Weekend Weather: Sunny with Mild Temperatures" → **3** (Regular weather forecast)

### ❌ NOT RELEVANT Articles (Score 1-3):

**Human Interest (No practical relevance):**
- "Local Resident Wins Game Show Prize" → **1** (Entertainment, not relevant)
- "Celebrity Visits City for Film Premiere" → **1** (Entertainment)
- "Local Artist Opens New Gallery Exhibition" → **1** (Arts, not relevant)

**Wrong Economic Focus:**
- "Stock Market Reaches New High" → **1** (Macro-economy, not microeconomy)
- "Bitcoin Price Surges" → **1** (Crypto speculation)
- "Company Reports Record Profits" → **1** (Business news without consumer impact)

**Explicitly Ignored:**
- "Local Team Wins Soccer Championship" → **1** (Sports)
- "Traffic Accident Closes Highway Lane" → **1** (Traffic accident)
- "New Restaurant Opens in Shopping Center" → **1** (Food venue)
- "Mayor Announces Park Renovation" → **1** (Not relevant unless health/weather related)

## Critical Filtering Instructions

**When analyzing articles:**

1. **First check the ignore list** - If it matches, score 1-2 immediately
2. **Identify the specific topic** - Don't make loose connections
3. **Verify direct relevance** - "Local person wins something" is NOT a tech event
4. **Consider practical impact** - How does this affect regular people's daily lives?
5. **Be strict** - When in doubt, score LOW (false negatives better than false positives)

**Technology MUST be actual technology** - Not just "a local achievement" or "someone doing something"
**Microeconomy MUST affect household budgets** - Not stock markets or big business profits
**Health MUST be actionable** - Outbreaks, alerts, access issues (not general medical science)
**Weather MUST be extreme or emergency** - Not routine forecasts

**Remember: Prefer to MISS an article rather than send an irrelevant one.**
