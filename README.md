# Copart Compensation Analysis

Interactive dashboard comparing competitive wages across ~197 Copart US locations against Walmart and Home Depot.

## Quick Start

```bash
python3 scripts/generate_data.py   # Generate wage data CSVs + data.json
python3 scripts/build_site.py      # Build HTML dashboard
```

Then open `public/index.html` in a browser, or deploy to Vercel:

```bash
npx vercel --prod
```

## Data Sources

| Source | What | Freshness |
|--------|------|-----------|
| [BLS OES](https://www.bls.gov/oes/current/oes537062.htm) | Market wage percentiles by state (SOC 53-7062, 43-9061) | May 2024 survey |
| [BEA RPP](https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area) | Regional Price Parities for state-level adjustment | 2023 |
| [Walmart](https://corporate.walmart.com/askwalmart/how-much-do-walmart-associates-make) | Stocking/Unloading + Cashier wages | Q1 2026 |
| [Home Depot](https://www.indeed.com/cmp/The-Home-Depot/salaries/Lot-Attendant) | Lot Associate + Cashier wages | Q1 2026 |

## Auditability

Every dollar figure in the dashboard is a clickable hyperlink to its underlying source (BLS OES state page, Indeed salary page, or corporate disclosure).

## Methodology

National BLS OES benchmarks are adjusted to state level using BEA Regional Price Parities. Employer minimum wage floors (Walmart $14/hr, Home Depot $15/hr) and state minimum wages are enforced. See the Methodology section in the dashboard for full details.
