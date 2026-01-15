#!/usr/bin/env python3
"""
Fetch World Bank Historical Income Classifications

This script fetches:
1. Current income classifications from World Bank API
2. Historical GNI per capita data (NY.GNP.PCAP.CD)
3. Applies historical thresholds to classify each country-year

Output: data/metadata/income_classifications.json
"""

import json
import time
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "metadata" / "income_classifications.json"
CANONICAL_COUNTRIES_DIR = DATA_DIR / "v3_1_temporal_graphs" / "countries"

# World Bank API endpoints
WB_COUNTRIES_URL = "https://api.worldbank.org/v2/country?format=json&per_page=300"
WB_INDICATOR_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000&date={start}:{end}"

# GNI per capita indicator (Atlas method, current USD)
GNI_INDICATOR = "NY.GNP.PCAP.CD"

# World Bank income thresholds (historical, updated annually)
# Source: https://datahelpdesk.worldbank.org/knowledgebase/articles/378833
INCOME_THRESHOLDS = {
    # Format: (low_upper, lower_middle_upper, upper_middle_upper)
    # Low: <= low_upper, Lower-middle: low_upper+1 to lower_middle_upper
    # Upper-middle: lower_middle_upper+1 to upper_middle_upper, High: > upper_middle_upper
    1990: (610, 2465, 7620),
    1991: (635, 2555, 7910),
    1992: (675, 2695, 8355),
    1993: (695, 2785, 8625),
    1994: (725, 2895, 8955),
    1995: (765, 3035, 9385),
    1996: (785, 3115, 9635),
    1997: (785, 3125, 9655),
    1998: (760, 3030, 9360),
    1999: (755, 2995, 9265),
    2000: (755, 2995, 9265),
    2001: (745, 2975, 9205),
    2002: (735, 2935, 9075),
    2003: (765, 3035, 9385),
    2004: (825, 3255, 10065),
    2005: (875, 3465, 10725),
    2006: (905, 3595, 11115),
    2007: (935, 3705, 11455),
    2008: (975, 3855, 11905),
    2009: (995, 3945, 12195),
    2010: (1005, 3975, 12275),
    2011: (1025, 4035, 12475),
    2012: (1035, 4085, 12615),
    2013: (1045, 4125, 12745),
    2014: (1045, 4125, 12745),
    2015: (1025, 4035, 12475),
    2016: (1005, 3955, 12235),
    2017: (995, 3895, 12055),
    2018: (1025, 3995, 12375),
    2019: (1035, 4045, 12535),
    2020: (1045, 4095, 12695),
    2021: (1045, 4095, 12695),
    2022: (1085, 4255, 13205),
    2023: (1135, 4465, 13845),
    2024: (1145, 4515, 14005),
}

# Country name mapping (Our canonical names → World Bank names)
CANONICAL_TO_WB = {
    "Cape Verde": "Cabo Verde",
    "Czech Republic": "Czechia",
    "Hong Kong": "Hong Kong SAR, China",
    "Ivory Coast": "Cote d'Ivoire",
    "Kyrgyzstan": "Kyrgyz Republic",
    "Laos": "Lao PDR",
    "North Korea": "Korea, Dem. People's Rep.",
    "Republic of the Congo": "Congo, Rep.",
    "Russia": "Russian Federation",
    "Slovakia": "Slovak Republic",
    "Swaziland": "Eswatini",
    "Syria": "Syrian Arab Republic",
    "Taiwan": "Taiwan, China",
    "The Gambia": "Gambia, The",
    "Türkiye": "Turkiye",
    "Turkey": "Turkiye",
    "Vietnam": "Viet Nam",
    "Yemen": "Yemen, Rep.",
}

# Legacy mappings (WB names for reference)
WB_NAME_MAP = {
    "Bahamas, The": "Bahamas, The",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Brunei Darussalam": "Brunei Darussalam",
    "Cabo Verde": "Cabo Verde",
    "Congo, Dem. Rep.": "Congo, Dem. Rep.",
    "Congo, Rep.": "Congo, Rep.",
    "Cote d'Ivoire": "Cote d'Ivoire",
    "Czechia": "Czech Republic",
    "Egypt, Arab Rep.": "Egypt, Arab Rep.",
    "Eswatini": "Eswatini",
    "Gambia, The": "Gambia, The",
    "Hong Kong SAR, China": "Hong Kong SAR, China",
    "Iran, Islamic Rep.": "Iran, Islamic Rep.",
    "Korea, Dem. People's Rep.": "Korea, Dem. People's Rep.",
    "Korea, Rep.": "Korea, Rep.",
    "Kyrgyz Republic": "Kyrgyz Republic",
    "Lao PDR": "Lao PDR",
    "Macao SAR, China": "Macao SAR, China",
    "Micronesia, Fed. Sts.": "Micronesia, Fed. Sts.",
    "North Macedonia": "North Macedonia",
    "Russian Federation": "Russian Federation",
    "Slovak Republic": "Slovak Republic",
    "St. Kitts and Nevis": "St. Kitts and Nevis",
    "St. Lucia": "St. Lucia",
    "St. Vincent and the Grenadines": "St. Vincent and the Grenadines",
    "Syrian Arab Republic": "Syrian Arab Republic",
    "Taiwan, China": "Taiwan, China",
    "Turkiye": "Turkey",
    "United States": "United States",
    "Venezuela, RB": "Venezuela",
    "Viet Nam": "Vietnam",
    "Yemen, Rep.": "Yemen, Rep.",
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def get_canonical_countries():
    """Get our canonical list of 178 countries."""
    if CANONICAL_COUNTRIES_DIR.exists():
        return sorted([d.name for d in CANONICAL_COUNTRIES_DIR.iterdir() if d.is_dir()])
    return []


def fetch_wb_countries():
    """Fetch all World Bank country info including current classification."""
    log("Fetching World Bank country list...")

    response = requests.get(WB_COUNTRIES_URL)
    response.raise_for_status()

    data = response.json()
    if len(data) < 2:
        raise ValueError("Unexpected API response format")

    countries = {}
    for country in data[1]:
        if country.get('region', {}).get('id') != 'NA':  # Exclude aggregates
            name = country['name']
            iso3 = country['id']
            income_level = country.get('incomeLevel', {}).get('id', 'Unknown')

            # Map income level codes
            income_map = {
                'LIC': 'Low income',
                'LMC': 'Lower middle income',
                'UMC': 'Upper middle income',
                'HIC': 'High income',
                'INX': 'Unknown'
            }

            countries[name] = {
                'iso3': iso3,
                'current_classification': income_map.get(income_level, 'Unknown')
            }

    log(f"  Found {len(countries)} countries")
    return countries


def fetch_gni_data(start_year=1990, end_year=2024):
    """Fetch historical GNI per capita data."""
    log(f"Fetching GNI per capita data ({start_year}-{end_year})...")

    url = WB_INDICATOR_URL.format(
        indicator=GNI_INDICATOR,
        start=start_year,
        end=end_year
    )

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    if len(data) < 2:
        raise ValueError("Unexpected API response format")

    gni_data = {}
    for record in data[1]:
        if record['value'] is not None:
            country_name = record['country']['value']
            year = int(record['date'])
            gni = float(record['value'])

            if country_name not in gni_data:
                gni_data[country_name] = {}
            gni_data[country_name][year] = gni

    log(f"  Found GNI data for {len(gni_data)} countries")
    return gni_data


def classify_by_gni(gni, year):
    """Classify a country based on GNI per capita and year-specific thresholds."""
    if gni is None or pd.isna(gni):
        return None

    # Get thresholds for this year (or nearest available)
    if year in INCOME_THRESHOLDS:
        low_upper, lm_upper, um_upper = INCOME_THRESHOLDS[year]
    else:
        # Use nearest year's thresholds
        available_years = sorted(INCOME_THRESHOLDS.keys())
        if year < available_years[0]:
            low_upper, lm_upper, um_upper = INCOME_THRESHOLDS[available_years[0]]
        else:
            low_upper, lm_upper, um_upper = INCOME_THRESHOLDS[available_years[-1]]

    if gni <= low_upper:
        return 'Low income'
    elif gni <= lm_upper:
        return 'Lower middle income'
    elif gni <= um_upper:
        return 'Upper middle income'
    else:
        return 'High income'


def map_to_3_groups(wb_classification):
    """Map World Bank 4-tier classification to our 3-tier groups."""
    mapping = {
        'Low income': 'Developing',
        'Lower middle income': 'Developing',
        'Upper middle income': 'Emerging',
        'High income': 'Advanced',
        'Unknown': 'Unknown'
    }
    return mapping.get(wb_classification, 'Unknown')


def main():
    log("=" * 60)
    log("FETCH WORLD BANK INCOME CLASSIFICATIONS")
    log("=" * 60)

    # Get canonical country list
    canonical_countries = get_canonical_countries()
    log(f"\nCanonical countries: {len(canonical_countries)}")

    # Fetch World Bank data
    wb_countries = fetch_wb_countries()
    gni_data = fetch_gni_data(1990, 2024)

    # Build classification data structure
    classifications = {
        'metadata': {
            'source': 'World Bank API',
            'indicator': 'NY.GNP.PCAP.CD (GNI per capita, Atlas method)',
            'fetch_date': datetime.now().isoformat(),
            'years': list(range(1990, 2025)),
            'groups': {
                'Developing': 'Low income + Lower middle income',
                'Emerging': 'Upper middle income',
                'Advanced': 'High income'
            }
        },
        'thresholds': {str(k): v for k, v in INCOME_THRESHOLDS.items()},
        'countries': {}
    }

    # Process each canonical country
    log("\nProcessing countries...")

    matched = 0
    unmatched = []

    for country in canonical_countries:
        # Try to find matching WB country
        wb_name = CANONICAL_TO_WB.get(country, country)

        if wb_name in wb_countries or country in wb_countries:
            lookup_name = wb_name if wb_name in wb_countries else country
            matched += 1

            country_info = {
                'wb_name': lookup_name,
                'iso3': wb_countries[lookup_name]['iso3'],
                'current_classification_4tier': wb_countries[lookup_name]['current_classification'],
                'current_classification_3tier': map_to_3_groups(wb_countries[lookup_name]['current_classification']),
                'by_year': {}
            }

            # Get historical classification from GNI data
            gni_lookup = gni_data.get(lookup_name, {})

            transitions = []
            prev_group = None

            for year in range(1990, 2025):
                gni = gni_lookup.get(year)

                if gni is not None:
                    wb_class = classify_by_gni(gni, year)
                    group_3tier = map_to_3_groups(wb_class)

                    country_info['by_year'][year] = {
                        'gni_per_capita': round(gni, 2),
                        'classification_4tier': wb_class,
                        'classification_3tier': group_3tier
                    }

                    # Track transitions
                    if prev_group is not None and group_3tier != prev_group:
                        transitions.append({
                            'year': year,
                            'from': prev_group,
                            'to': group_3tier
                        })
                    prev_group = group_3tier
                else:
                    # No GNI data - use current classification as fallback
                    country_info['by_year'][year] = {
                        'gni_per_capita': None,
                        'classification_4tier': None,
                        'classification_3tier': None  # Will be interpolated
                    }

            country_info['transitions'] = transitions
            classifications['countries'][country] = country_info

        else:
            unmatched.append(country)
            # Add with unknown classification
            classifications['countries'][country] = {
                'wb_name': None,
                'iso3': None,
                'current_classification_4tier': 'Unknown',
                'current_classification_3tier': 'Unknown',
                'by_year': {year: {'gni_per_capita': None, 'classification_4tier': None, 'classification_3tier': None} for year in range(1990, 2025)},
                'transitions': []
            }

    log(f"\n  Matched: {matched} countries")
    log(f"  Unmatched: {len(unmatched)} countries")
    if unmatched:
        log(f"  Unmatched list: {unmatched[:10]}{'...' if len(unmatched) > 10 else ''}")

    # Interpolate missing years (forward fill, then backward fill)
    log("\nInterpolating missing years...")
    for country, info in classifications['countries'].items():
        if info['wb_name'] is None:
            continue

        years = sorted(info['by_year'].keys())

        # Forward fill
        last_known = None
        for year in years:
            if info['by_year'][year]['classification_3tier'] is not None:
                last_known = info['by_year'][year]
            elif last_known is not None:
                info['by_year'][year]['classification_3tier'] = last_known['classification_3tier']
                info['by_year'][year]['classification_4tier'] = last_known['classification_4tier']
                info['by_year'][year]['interpolated'] = True

        # Backward fill
        last_known = None
        for year in reversed(years):
            if info['by_year'][year]['classification_3tier'] is not None:
                last_known = info['by_year'][year]
            elif last_known is not None:
                info['by_year'][year]['classification_3tier'] = last_known['classification_3tier']
                info['by_year'][year]['classification_4tier'] = last_known['classification_4tier']
                info['by_year'][year]['interpolated'] = True

    # Generate summary statistics
    log("\nGenerating summary statistics...")

    summary = {'by_year': {}}
    for year in range(1990, 2025):
        groups = {'Developing': 0, 'Emerging': 0, 'Advanced': 0, 'Unknown': 0}
        for country, info in classifications['countries'].items():
            group = info['by_year'].get(year, {}).get('classification_3tier', 'Unknown')
            if group is None:
                group = 'Unknown'
            groups[group] += 1
        summary['by_year'][year] = groups

    classifications['summary'] = summary

    # Show transitions
    log("\nCountries with transitions:")
    transition_count = 0
    for country, info in classifications['countries'].items():
        if info['transitions']:
            transition_count += 1
            for t in info['transitions']:
                log(f"  {country}: {t['from']} → {t['to']} ({t['year']})")
    log(f"\nTotal countries with transitions: {transition_count}")

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(classifications, f, indent=2)

    log(f"\nSaved to: {OUTPUT_PATH}")

    # Print summary table
    log("\n" + "=" * 60)
    log("GROUP SIZES BY DECADE")
    log("=" * 60)
    log(f"{'Year':<8} {'Developing':<12} {'Emerging':<12} {'Advanced':<12} {'Unknown':<10}")
    log("-" * 54)
    for year in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
        s = summary['by_year'].get(year, {})
        log(f"{year:<8} {s.get('Developing', 0):<12} {s.get('Emerging', 0):<12} {s.get('Advanced', 0):<12} {s.get('Unknown', 0):<10}")

    log("\n" + "=" * 60)
    log("COMPLETE")
    log("=" * 60)


if __name__ == '__main__':
    main()
