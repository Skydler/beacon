# My News Preferences

This file defines what types of news articles are relevant to me. The LLM uses this as context to filter articles.

## Geographic Focus

- **Primary**: Quilmes (including Quilmes Este, Ezpeleta, Berazategui, and surrounding areas)
- **Secondary**: Argentina-wide news, but ONLY when it has direct impact on my daily life in Quilmes

### What "national impact" means:
- Economic policy changes (inflation, currency, wages, subsidies, taxes)
- National health alerts or disease outbreaks
- Laws or regulations that affect residents directly
- Severe weather systems that will reach the Buenos Aires / Quilmes area
- National infrastructure or utility decisions that affect my region

### What national news to IGNORE:
- Events happening in other provinces with no local effect
- Local news from other cities (e.g., a new building in Cordoba, flooding in Tucuman)
- National political drama without concrete policy impact
- National sports, entertainment, or cultural events

## High Priority Topics

### Quilmes Local News
- **Climate & Weather**: Weather events affecting Quilmes, storms, heat waves, flooding, alerts
- **New Buildings & Urban Development**: Construction projects, new buildings, commercial developments, rezoning
- **Road Work & Infrastructure**: Street repairs, paving, new roads, bridge work, utility infrastructure, traffic signals, drainage
- **Local Economy**: Store openings/closings, local business news, commercial activity in the area
- **Public Services**: Changes in local services, transportation, utilities

### Economy (Local + National Impact)
- **Cost of Living**: Price increases/decreases (food, gas, utilities, rent)
- **Wages & Employment**: Minimum wage changes, job market, unemployment, layoffs
- **Economic Policy**: Inflation measures, currency changes, subsidies, tax changes that affect households
- **Utility Rates**: Electricity, gas, water rate changes
- **Banking & Consumer Finance**: Account fees, credit access, payment systems changes

### Health
- **Disease Outbreaks**: COVID, dengue, flu outbreaks (local or national)
- **Public Health Alerts**: Vaccination campaigns, health warnings, contamination alerts
- **Healthcare Access**: Hospital capacity, healthcare system changes affecting Quilmes residents

### Technology & Digital
- **Cybersecurity**: Data breaches, security advisories, malware, hacking incidents
- **Local Tech Events**: Conferences, meetups, hackathons in the area
- **Internet & Connectivity**: Broadband, network outages, ISP news affecting my area
- **Open Source**: Notable FOSS releases, open source community news

### Food & Dining (Quilmes Area)
- **Restaurant Openings**: New restaurants, bars, cafes opening in Quilmes area
- **Food Events**: Food festivals, culinary fairs, food markets in the area
- **Food Safety**: Health inspections, food recalls, contamination alerts

## Medium Priority Topics

- **Education Technology**: Coding bootcamps, online learning, school tech programs
- **Healthcare Technology**: Telemedicine, health apps
- **Government Digital Services**: Online services, e-government initiatives
- **Consumer Rights**: Regulatory changes, recalls
- **Mental Health**: Services and support programs available locally

## Low Priority Topics

Only notify me if these are major stories:

- **Regular Weather**: Normal forecasts (unless extreme or emergency)
- **Transportation**: Public transit updates (unless major disruption)
- **Environment**: Environmental initiatives (unless immediate health/safety impact)

## Topics to Ignore

Do NOT notify me about:

- **Sports** (unless esports/technology-related)
- **Celebrity gossip, entertainment, game shows**
- **Political campaigns and partisan politics** (unless direct policy impact on daily life)
- **Crime reports** (unless cybercrime, major security breach, or public safety alert)
- **Obituaries and funerals**
- **Human interest stories** without practical relevance
- **Traffic accidents** (unless major highway closure)
- **Stock market / Wall Street** (I care about microeconomy, not markets)
- **Crypto prices and trading**
- **Arts and culture events** (galleries, museums, concerts)
- **Real estate market trends** (unless affecting Quilmes rental prices significantly)
- **News from other provinces/cities** with no impact on Quilmes or national policy

## Specific Keywords

### High relevance keywords (boost score):

**Local/Quilmes:**
- Quilmes, Quilmes Este, Berazategui, Ezpeleta
- Obras, pavimentacion, construccion, edificio nuevo
- Corte de calle, desvio, obra vial

**Economy:**
- Price increase, inflation, cost of living, inflacion, aumento
- Minimum wage, salary, employment, salario, empleo
- Subsidy, financial aid, subsidio, bono
- Utility rates, gas prices, rent increase, tarifas, alquiler
- Layoffs, hiring, job market, despidos
- Dolar, tipo de cambio, devaluacion

**Technology:**
- Python, JavaScript, programming, software development
- AI/ML, artificial intelligence, machine learning
- Cybersecurity, InfoSec, hacking, malware, ransomware
- Linux, open source, FOSS
- Privacy, encryption, data protection
- Internet outage, network issues

**Health:**
- COVID, coronavirus, dengue, flu outbreak
- Vaccination, vaccine, immunization
- Disease outbreak, epidemic
- Hospital emergency, health alert
- Contamination, food safety

**Weather:**
- Storm warning, heat wave, extreme weather
- Flooding, evacuation, weather emergency
- Alerta meteorologica, tormenta, inundacion

**Food & Dining:**
- Restaurant opening, new restaurant, inauguracion
- Food festival, culinary fair, feria gastronomica
- Food market, farmers market

**Infrastructure:**
- Road paving, street repair, road improvement
- Bridge construction, infrastructure project
- Streetlight, sidewalk repair, drainage
- Asfalto, vereda, alumbrado, desague

### Negative keywords (reduce score):
- Casino, gambling, lottery
- Horoscope, astrology
- Wedding, engagement
- Fashion, makeup
- Awards ceremony (unless tech/science)
- Celebrity, influencer, reality TV
- Stock market, trading, investment tips
- Cryptocurrency speculation

## Scoring Guidance for LLM

Use this scale when rating articles:

- **10**: Urgent/critical for Quilmes residents (disease outbreak, severe weather warning, major security breach, major national economic shock)
- **8-9**: High-priority topic with direct local impact (price increases, Quilmes construction/roadwork, tech events, health alerts, restaurant openings nearby, major national economic policy change)
- **6-7**: Medium-priority topic with clear relevance (tech business, healthcare access, service changes, infrastructure improvements, national news with indirect local impact)
- **4-5**: Low-priority topic or weak local connection
- **2-3**: Marginally relevant or contains negative keywords
- **1**: Should be ignored based on ignore list

### Geographic Scoring Rules

- **Quilmes / Quilmes Este / Berazategui / Ezpeleta**: +1 to +2 boost on already-relevant articles (don't exceed 10)
- **Other Buenos Aires suburbs**: No boost, score on merit
- **Other provinces**: Score 1-2 UNLESS it's a national-level story that affects Quilmes residents (economic policy, national health alert, etc.)

## Critical Filtering Instructions

**When analyzing articles:**

1. **First check geography** - Is this about Quilmes or national-impact news? If it's local news from another city/province, score 1-2
2. **Check the ignore list** - If it matches, score 1-2 immediately
3. **Identify the specific topic** - Don't make loose connections
4. **Consider practical impact** - How does this affect me in Quilmes?
5. **Be strict** - When in doubt, score LOW (false negatives better than false positives)

**National news filter**: Only include national news if it will change something in my daily life (prices, services, health, regulations). Political maneuvering, other cities' local problems, or abstract macro trends without household impact should be scored low.

**Remember: Prefer to MISS an article rather than send an irrelevant one.**
