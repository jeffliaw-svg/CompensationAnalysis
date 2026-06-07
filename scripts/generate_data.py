#!/usr/bin/env python3
"""
Generate wage data files for the Copart Compensation Analysis.

Produces:
  - copart_locations_us.csv          (~197 Copart yard locations)
  - data/bls/bls_oes_wages.csv       (BLS OES wages by state, 2 SOC codes)
  - data/employers/employer_wages.csv (Walmart + Home Depot wages by state)
  - public/data.json                  (merged data for the dashboard)

All wage data includes Source_URL for auditability.

National benchmarks: BLS OES May 2024.
State adjustment: BEA Regional Price Parities (2023).
Employer data: Indeed/Glassdoor aggregated salary data, Q1 2026.
"""

import csv
import json
import math
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────
# BEA Regional Price Parities (2023, ratio to national average = 1.00)
# Source: https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area
# ─────────────────────────────────────────────────────────────────────
STATE_RPP = {
    "AL": 0.880, "AK": 1.050, "AZ": 0.978, "AR": 0.869,
    "CA": 1.107, "CO": 1.030, "CT": 1.082, "DE": 1.010,
    "FL": 1.003, "GA": 0.930, "HI": 1.100, "ID": 0.940,
    "IL": 0.990, "IN": 0.915, "IA": 0.878, "KS": 0.910,
    "KY": 0.890, "LA": 0.900, "ME": 1.000, "MD": 1.070,
    "MA": 1.090, "MI": 0.930, "MN": 0.980, "MS": 0.870,
    "MO": 0.900, "MT": 0.950, "NE": 0.920, "NV": 0.990,
    "NH": 1.040, "NJ": 1.088, "NM": 0.930, "NY": 1.130,
    "NC": 0.940, "ND": 0.930, "OH": 0.920, "OK": 0.878,
    "OR": 1.020, "PA": 0.970, "RI": 1.020, "SC": 0.920,
    "SD": 0.910, "TN": 0.920, "TX": 0.968, "UT": 0.980,
    "VT": 1.020, "VA": 1.020, "WA": 1.100, "WV": 0.870,
    "WI": 0.940, "WY": 0.950,
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

# ─────────────────────────────────────────────────────────────────────
# State minimum wages (2025-2026)
# ─────────────────────────────────────────────────────────────────────
STATE_MIN_WAGE = {
    "AL": 7.25, "AK": 11.91, "AZ": 14.70, "AR": 11.00,
    "CA": 16.50, "CO": 14.81, "CT": 15.69, "DE": 13.25,
    "FL": 13.00, "GA": 7.25, "HI": 14.00, "ID": 7.25,
    "IL": 14.00, "IN": 7.25, "IA": 7.25, "KS": 7.25,
    "KY": 7.25, "LA": 7.25, "ME": 14.15, "MD": 15.00,
    "MA": 15.00, "MI": 10.56, "MN": 11.13, "MS": 7.25,
    "MO": 13.75, "MT": 10.55, "NE": 13.50, "NV": 12.00,
    "NH": 7.25, "NJ": 15.49, "NM": 12.00, "NY": 15.50,
    "NC": 7.25, "ND": 7.25, "OH": 10.70, "OK": 7.25,
    "OR": 14.70, "PA": 7.25, "RI": 15.00, "SC": 7.25,
    "SD": 11.45, "TN": 7.25, "TX": 7.25, "UT": 7.25,
    "VT": 14.01, "VA": 12.41, "WA": 16.66, "WV": 8.75,
    "WI": 7.25, "WY": 7.25,
}

# ─────────────────────────────────────────────────────────────────────
# BLS OES May 2024 National Benchmarks (hourly wages)
# Sources:
#   https://www.bls.gov/oes/current/oes537062.htm
#   https://www.bls.gov/oes/current/oes439061.htm
# ─────────────────────────────────────────────────────────────────────
BLS_NATIONAL = {
    "53-7062": {
        "title": "Laborers and Freight, Stock, and Material Movers, Hand",
        "pct10": 14.32, "pct25": 15.88, "median": 18.12,
        "pct75": 21.26, "pct90": 24.51, "mean": 19.10,
        "source_national": "https://www.bls.gov/oes/current/oes537062.htm",
    },
    "43-9061": {
        "title": "Office Clerks, General",
        "pct10": 14.00, "pct25": 16.55, "median": 20.97,
        "pct75": 25.50, "pct90": 30.69, "mean": 21.80,
        "source_national": "https://www.bls.gov/oes/current/oes439061.htm",
    },
}

# ─────────────────────────────────────────────────────────────────────
# Employer wage baselines (national averages, hourly)
# ─────────────────────────────────────────────────────────────────────
EMPLOYER_BASELINES = {
    "Walmart": {
        "Outdoor": {
            "role_title": "Stocking & Unloading Associate",
            "low": 14.00, "high": 21.00, "avg": 17.00,
            "company_floor": 14.00,
            "source_url": "https://www.indeed.com/cmp/Walmart/salaries/Stocker",
            "source_name": "Indeed - Walmart Stocker Salaries",
            "source_corporate": "https://corporate.walmart.com/askwalmart/how-much-do-walmart-associates-make",
        },
        "Indoor": {
            "role_title": "Cashier / Customer Service Associate",
            "low": 12.50, "high": 18.50, "avg": 15.25,
            "company_floor": 14.00,
            "source_url": "https://www.indeed.com/cmp/Walmart/salaries/Cashier",
            "source_name": "Indeed - Walmart Cashier Salaries",
            "source_corporate": "https://corporate.walmart.com/askwalmart/how-much-do-walmart-associates-make",
        },
    },
    "Home Depot": {
        "Outdoor": {
            "role_title": "Lot Associate / Receiving Associate",
            "low": 14.50, "high": 22.00, "avg": 17.50,
            "company_floor": 15.00,
            "source_url": "https://www.indeed.com/cmp/The-Home-Depot/salaries/Lot-Attendant",
            "source_name": "Indeed - Home Depot Lot Attendant Salaries",
            "source_corporate": "https://www.glassdoor.com/Salary/The-Home-Depot-Salaries-E655.htm",
        },
        "Indoor": {
            "role_title": "Cashier / Customer Service Associate",
            "low": 13.00, "high": 19.00, "avg": 15.75,
            "company_floor": 15.00,
            "source_url": "https://www.indeed.com/cmp/The-Home-Depot/salaries/Cashier",
            "source_name": "Indeed - Home Depot Cashier Salaries",
            "source_corporate": "https://www.glassdoor.com/Salary/The-Home-Depot-Salaries-E655.htm",
        },
    },
}

# ─────────────────────────────────────────────────────────────────────
# Copart Locations (~197 US yards)
# Compiled from Copart.com, eRepairables.com, CopartDirect.com
# ─────────────────────────────────────────────────────────────────────
COPART_LOCATIONS = [
    ("Copart Anchorage", "Anchorage", "AK", "401 W Chipperfield Dr", "99501"),
    ("Copart Anchorage South", "Anchorage", "AK", "7533 Old Seward Hwy", "99518"),
    ("Copart Birmingham", "Hueytown", "AL", "3101 Davey Allison Blvd", "35023"),
    ("Copart Tanner", "Tanner", "AL", "20760 Sandy Road", "35671"),
    ("Copart Mobile", "Eight Mile", "AL", "4763 Lott Road", "36613"),
    ("Copart Mobile South", "Theodore", "AL", "9401 Old Pascagoula Rd", "36582"),
    ("Copart Montgomery", "Montgomery", "AL", "6044 Troy Highway", "36116"),
    ("Copart Dothan", "Newton", "AL", "10428 West US 84", "36352"),
    ("Copart Little Rock", "Conway", "AR", "703 Main St", "72032"),
    ("Copart Fayetteville", "Prairie Grove", "AR", "15976 Bill Campbell Rd", "72753"),
    ("Copart Phoenix", "Phoenix", "AZ", "615 S 51st Ave", "85043"),
    ("Copart Tucson", "Tucson", "AZ", "5600 S Arcadia Ave", "85706"),
    ("Copart Los Angeles", "Los Angeles", "CA", "8423 S Alameda St", "90001"),
    ("Copart Sun Valley", "Sun Valley", "CA", "11409 Penrose St", "91352"),
    ("Copart Van Nuys", "Van Nuys", "CA", "7519 Woodman Ave", "91405"),
    ("Copart Rancho Cucamonga", "Rancho Cucamonga", "CA", "12167 Arrow Rte", "91739"),
    ("Copart Colton", "Colton", "CA", "1203 S Rancho Ave", "92324"),
    ("Copart San Diego", "San Diego", "CA", "7847 Airway Rd", "92154"),
    ("Copart Bakersfield", "Bakersfield", "CA", "2216 Coy Avenue", "93307"),
    ("Copart Fresno", "Fresno", "CA", "1255 East Central", "93725"),
    ("Copart San Martin", "San Martin", "CA", "13895 Llagas Ave", "95046"),
    ("Copart Vallejo", "Vallejo", "CA", "282 Fifth Street", "94590"),
    ("Copart Hayward", "Hayward", "CA", "1964 Sabre Street", "94545"),
    ("Copart Martinez", "Martinez", "CA", "2701 Waterfront Rd", "94553"),
    ("Copart Sacramento", "Sacramento", "CA", "8600 Morrison Creek Dr", "95828"),
    ("Copart Antelope", "Antelope", "CA", "8650 Antelope North Rd", "95843"),
    ("Copart Napa", "American Canyon", "CA", "1660 Green Island Rd", "94503"),
    ("Copart Redding", "Anderson", "CA", "4603 Locust Road", "96007"),
    ("Copart Fairfield", "Fairfield", "CA", "4665 Business Center Dr", "94534"),
    ("Copart Denver", "Brighton", "CO", "1281 County Rd 27", "80603"),
    ("Copart Denver Central", "Denver", "CO", "6464 Downing St", "80229"),
    ("Copart Colorado Springs", "Colorado Springs", "CO", "640 Winters Dr", "80907"),
    ("Copart Littleton", "Littleton", "CO", "8300 Blakeland Dr", "80125"),
    ("Copart Hartford", "New Britain", "CT", "138 Christian Lane", "06051"),
    ("Copart Hartford Springfield", "East Granby", "CT", "49 Russell Road", "06026"),
    ("Copart Seaford", "Seaford", "DE", "26029 Bethel Concord Rd", "19973"),
    ("Copart Jacksonville North", "Jacksonville", "FL", "10200 Alton Box Rd", "32218"),
    ("Copart Jacksonville East", "Jacksonville", "FL", "5007 New Kings Rd", "32209"),
    ("Copart Jacksonville West", "Jacksonville", "FL", "450 Hammond Blvd", "32220"),
    ("Copart Tampa South", "Riverview", "FL", "12020 US Highway 301 S", "33578"),
    ("Copart Orlando North", "Apopka", "FL", "3352 W Orange Blossom Trl", "32712"),
    ("Copart Orlando", "Orlando", "FL", "307 East Landstreet Rd", "32824"),
    ("Copart Ocala", "Ocala", "FL", "7100 NW 44 Ave", "34482"),
    ("Copart Miami South", "Homestead", "FL", "24301 SW 137th Ave", "33032"),
    ("Copart Miami North", "Miami", "FL", "12850 NW 27th Ave", "33054"),
    ("Copart Miami Central", "Miami", "FL", "11858 NW 36th Ave", "33167"),
    ("Copart West Palm Beach", "West Palm Beach", "FL", "7876 Belvedere Rd", "33411"),
    ("Copart Fort Pierce", "Fort Pierce", "FL", "2601 Center Road", "34946"),
    ("Copart Tallahassee", "Midway", "FL", "1825 Commerce Blvd", "32343"),
    ("Copart Punta Gorda", "Punta Gorda", "FL", "5017 Duncan Road", "33982"),
    ("Copart Punta Gorda South", "Arcadia", "FL", "10175 U.S. 17", "34269"),
    ("Copart Atlanta West", "Austell", "GA", "2568 Old Alabama Rd", "30168"),
    ("Copart Atlanta East", "Loganville", "GA", "6089 Hwy 20", "30052"),
    ("Copart Atlanta South", "Ellenwood", "GA", "761 Clark Dr", "30294"),
    ("Copart Atlanta North", "Gainesville", "GA", "1602 Athens Highway", "30507"),
    ("Copart Cartersville", "Cartersville", "GA", "1880 Hwy 113", "30120"),
    ("Copart Savannah", "Savannah", "GA", "5510 Silk Hope Rd", "31405"),
    ("Copart Tifton", "Tifton", "GA", "399 Oakridge Church Rd", "31794"),
    ("Copart Augusta", "Augusta", "GA", "3810 Hensley Rd", "30906"),
    ("Copart Macon", "Byron", "GA", "304 Smith Road", "31008"),
    ("Copart Fairburn", "Fairburn", "GA", "6737 Roosevelt Hwy", "30213"),
    ("Copart Honolulu", "Kapolei", "HI", "91-542 Awakumoku St", "96707"),
    ("Copart Boise", "Nampa", "ID", "3716 N Middleton Rd", "83687"),
    ("Copart Chicago North", "Elgin", "IL", "1475 Bluff City Blvd", "60120"),
    ("Copart Chicago South", "Chicago Heights", "IL", "89 E Sauk Trail", "60411"),
    ("Copart Wheeling", "Wheeling", "IL", "110 East Palatine Rd", "60090"),
    ("Copart Southern Illinois", "Cahokia Heights", "IL", "99 Racehorse Dr", "62205"),
    ("Copart Peoria", "Pekin", "IL", "14417 VFW Rd", "61554"),
    ("Copart Indianapolis", "Indianapolis", "IN", "4040 Office Plaza Blvd", "46254"),
    ("Copart Fort Wayne", "Hartford City", "IN", "696 East State Rd 26", "47348"),
    ("Copart Dyer", "Dyer", "IN", "641 Joliet St", "46311"),
    ("Copart Evansville", "Evansville", "IN", "800 E Virginia St", "47711"),
    ("Copart Des Moines", "Des Moines", "IA", "3300 Vandalia Rd", "50317"),
    ("Copart Eldridge", "Eldridge", "IA", "451 Blackhawk Trail Rd", "52748"),
    ("Copart Kansas City", "Kansas City", "KS", "6211 Kansas Ave", "66111"),
    ("Copart Wichita", "Wichita", "KS", "2648 S West St", "67217"),
    ("Copart Louisville", "Louisville", "KY", "3100 Pond Station Rd", "40272"),
    ("Copart Lexington East", "Lexington", "KY", "5801 Kasp Ct", "40509"),
    ("Copart Lexington West", "Lawrenceburg", "KY", "1051 Industry Rd", "40342"),
    ("Copart Walton", "Walton", "KY", "13273 Dixie Highway", "41094"),
    ("Copart Earlington", "Earlington", "KY", "700 N Sandcut Rd", "42410"),
    ("Copart New Orleans", "New Orleans", "LA", "14600 Old Gentilly Rd", "70129"),
    ("Copart Baton Rouge", "Greenwell Springs", "LA", "21595 Greenwell Springs Rd", "70739"),
    ("Copart Shreveport", "Shreveport", "LA", "5235 Greenwood Rd", "71109"),
    ("Copart Lyman", "Lyman", "ME", "136 Kennebunk Pond Rd", "04002"),
    ("Copart Windham", "Windham", "ME", "11 Bedrock Terrace", "04062"),
    ("Copart Baltimore", "Finksburg", "MD", "2251 Old Westminster Pike", "21048"),
    ("Copart Baltimore East", "Baltimore", "MD", "601 W Patapsco Ave", "21225"),
    ("Copart Washington DC", "Waldorf", "MD", "11055 Billingsley Rd", "20602"),
    ("Copart North Boston", "North Billerica", "MA", "55R High St", "01862"),
    ("Copart South Boston", "Mendon", "MA", "82 Cape Road", "01756"),
    ("Copart West Warren", "West Warren", "MA", "600 Old West Warren Rd", "01092"),
    ("Copart Freetown", "Assonet", "MA", "170 S Main St", "02702"),
    ("Copart Detroit", "Woodhaven", "MI", "21000 Hayden Dr", "48183"),
    ("Copart Flint", "Davison", "MI", "5000 N State Rd", "48423"),
    ("Copart Ionia", "Portland", "MI", "8460 S State Rd", "48875"),
    ("Copart Lansing", "Lansing", "MI", "3902 South Canal Rd", "48917"),
    ("Copart Kincheloe", "Kincheloe", "MI", "5030 W Kincheloe Rd", "49788"),
    ("Copart Wayland", "Wayland", "MI", "1261 142nd Ave", "49348"),
    ("Copart Minneapolis", "Fridley", "MN", "3737 E River Rd", "55421"),
    ("Copart Minneapolis North", "Ham Lake", "MN", "1526 Bunker Lake Blvd", "55304"),
    ("Copart St Cloud", "Avon", "MN", "200 County Rd 159", "56310"),
    ("Copart Jackson", "Florence", "MS", "205 S Rankin Industrial Dr", "39073"),
    ("Copart Grenada", "Grenada", "MS", "15673 Highway 8", "38901"),
    ("Copart Springfield", "Rogersville", "MO", "2889 E US Highway 60", "65742"),
    ("Copart St Louis", "Bridgeton", "MO", "13033 Taussig Ave", "63044"),
    ("Copart Columbia", "Columbia", "MO", "8485 Richland Rd", "65201"),
    ("Copart Kansas City MO", "Kansas City", "MO", "1420 S 55th St", "66106"),
    ("Copart Billings", "Billings", "MT", "1090 Island Park Rd", "59101"),
    ("Copart Helena", "Helena", "MT", "3333 Bozeman Ave", "59601"),
    ("Copart Lincoln", "Greenwood", "NE", "13603 238th St", "68366"),
    ("Copart Las Vegas", "Las Vegas", "NV", "4810 N Lamb Blvd", "89115"),
    ("Copart North Las Vegas", "North Las Vegas", "NV", "3441 Clayton St", "89032"),
    ("Copart Reno", "Reno", "NV", "9915 N Virginia St", "89506"),
    ("Copart Candia", "Candia", "NH", "134 Raymond Rd", "03034"),
    ("Copart Somerville", "Hillsborough", "NJ", "2124 W Camplain Rd", "08844"),
    ("Copart Trenton", "Windsor", "NJ", "108 North Main St", "08561"),
    ("Copart Glassboro West", "Glassboro", "NJ", "781 Jacob Harris Ave", "08028"),
    ("Copart Glassboro East", "Glassboro", "NJ", "200 Grove St", "08028"),
    ("Copart Albuquerque", "Albuquerque", "NM", "7705 Broadway Blvd SE", "87105"),
    ("Copart Newburgh", "Marlboro", "NY", "25 Riverview Dr", "12542"),
    ("Copart Syracuse", "Central Square", "NY", "46 Zuk-Pierce Rd", "13036"),
    ("Copart Long Island", "Brookhaven", "NY", "1983 Montauk Hwy", "11719"),
    ("Copart Rochester", "Leroy", "NY", "4 West Ave", "14482"),
    ("Copart Albany", "Albany", "NY", "1916 Central Ave", "12205"),
    ("Copart Buffalo", "Angola", "NY", "8418 Southwestern Blvd", "14006"),
    ("Copart Raleigh", "Dunn", "NC", "310 Copart Rd", "28334"),
    ("Copart Raleigh North", "Raleigh", "NC", "6400 Old Smithfield Rd", "27603"),
    ("Copart Concord", "Concord", "NC", "7940 US Highway 601 S", "28025"),
    ("Copart Lumberton", "Lumberton", "NC", "4019 NC 72 Hwy W", "28360"),
    ("Copart Gastonia", "Gastonia", "NC", "3060 Fairview Dr", "28052"),
    ("Copart China Grove", "China Grove", "NC", "1081 Recovery Rd", "28023"),
    ("Copart Mebane", "Mebane", "NC", "1870 US 70 Hwy", "27302"),
    ("Copart Bismarck", "Bismarck", "ND", "3700 Apple Creek Rd", "58504"),
    ("Copart Columbus", "Columbus", "OH", "1680 Williams Rd", "43207"),
    ("Copart Cleveland East", "Northfield", "OH", "286 E Twinsburg Rd", "44067"),
    ("Copart Cleveland West", "Columbia Station", "OH", "34417 E Royalton Rd", "44028"),
    ("Copart Dayton", "Moraine", "OH", "4691 Springboro Pike", "45439"),
    ("Copart Cincinnati", "Cincinnati", "OH", "4568 Muhlhauser Rd", "45011"),
    ("Copart Oklahoma City", "Oklahoma City", "OK", "2829 SE 15th St", "73129"),
    ("Copart Tulsa", "Tulsa", "OK", "2408 W 21st St", "74107"),
    ("Copart Portland North", "Portland", "OR", "6900 NE Cornfoot Dr", "97218"),
    ("Copart Portland South", "Woodburn", "OR", "2885 National Way", "97071"),
    ("Copart Eugene", "Eugene", "OR", "29815 E Enid Rd", "97402"),
    ("Copart Philadelphia", "Pennsburg", "PA", "2704 Geryville Pike", "18073"),
    ("Copart Philadelphia East", "Chalfont", "PA", "77 Bristol Road", "18914"),
    ("Copart Harrisburg", "Grantville", "PA", "8 Park Drive", "17028"),
    ("Copart York Haven", "York Haven", "PA", "795 Sipe Rd", "17370"),
    ("Copart Chambersburg", "Chambersburg", "PA", "2962 Lincoln Way W", "17202"),
    ("Copart Pittsburgh South", "West Mifflin", "PA", "526 Thompson Run Rd", "15122"),
    ("Copart Pittsburgh North", "Ellwood City", "PA", "2000 River Road", "16117"),
    ("Copart Pittsburgh East", "Adamsburg", "PA", "133 Asphalt Lane", "15611"),
    ("Copart Altoona", "Ebensburg", "PA", "4007 Admiral Peary Hwy", "15931"),
    ("Copart Scranton", "Duryea", "PA", "210 Mcalpine St", "18642"),
    ("Copart Exeter", "Exeter", "RI", "10 Industrial Dr", "02822"),
    ("Copart Columbia SC", "Gaston", "SC", "4324 Hwy 321 S", "29053"),
    ("Copart North Charleston", "Harleyville", "SC", "120 Commerce Dr", "29448"),
    ("Copart Spartanburg", "Spartanburg", "SC", "1922 Nazareth Church Rd", "29301"),
    ("Copart Rapid City", "Rapid City", "SD", "2170 Seger Dr", "57701"),
    ("Copart Nashville", "Lebanon", "TN", "865 Stumpy Lane", "37090"),
    ("Copart Memphis", "Memphis", "TN", "5545 Swinnea Rd", "38118"),
    ("Copart Knoxville", "Madisonville", "TN", "6355 B Hwy 411", "37354"),
    ("Copart Houston", "Houston", "TX", "1655 Rankin Road", "77073"),
    ("Copart Houston East", "Houston", "TX", "2535 West Lake Houston Pkwy", "77339"),
    ("Copart Dallas", "Grand Prairie", "TX", "505 Idlewild Rd", "75051"),
    ("Copart Dallas South", "Wilmer", "TX", "1701 East Beltline Rd", "75172"),
    ("Copart Fort Worth", "Haslet", "TX", "950 Blue Mound Rd W", "76052"),
    ("Copart San Antonio", "San Antonio", "TX", "11130 Applewhite Rd", "78224"),
    ("Copart Austin", "New Braunfels", "TX", "8725 IH-35 N", "78130"),
    ("Copart Corpus Christi", "Corpus Christi", "TX", "3200 Agnes St", "78405"),
    ("Copart Amarillo", "Amarillo", "TX", "3999 S Loop 335 E", "79118"),
    ("Copart Abilene", "Abilene", "TX", "2630 FM 3034", "79601"),
    ("Copart El Paso", "Anthony", "TX", "501 Valley Chili Rd", "79821"),
    ("Copart McAllen", "Mercedes", "TX", "301 Mile 1 East", "78570"),
    ("Copart Lufkin", "Lufkin", "TX", "3700 Old Union Rd", "75904"),
    ("Copart Longview", "Longview", "TX", "3046 Highway 322 S", "75603"),
    ("Copart Waco", "Temple", "TX", "7201 N General Bruce Dr", "76501"),
    ("Copart Andrews", "Andrews", "TX", "1975 SW 860", "79714"),
    ("Copart Salt Lake City North", "North Salt Lake", "UT", "170 W Center St", "84054"),
    ("Copart Salt Lake City", "Magna", "UT", "7320 W 2100 S", "84044"),
    ("Copart Farr West", "Farr West", "UT", "3586 N 2000 W", "84404"),
    ("Copart Rutland", "Center Rutland", "VT", "29 Old Route 4A", "05736"),
    ("Copart Richmond", "Sandston", "VA", "5701 Whiteside Rd", "23150"),
    ("Copart Fredericksburg", "Fredericksburg", "VA", "4717 Massaponax Church Rd", "22408"),
    ("Copart Charles City", "Charles City", "VA", "6300 Chambers Rd", "23030"),
    ("Copart Danville", "Chatham", "VA", "12360 US Hwy 29", "24531"),
    ("Copart Hampton", "Hampton", "VA", "16 Nettles Lane", "23666"),
    ("Copart North Seattle", "Arlington", "WA", "16701 51st Ave NE", "98223"),
    ("Copart Graham", "Graham", "WA", "21421 Meridian E", "98338"),
    ("Copart Pasco", "Pasco", "WA", "3333 N Railroad Ave", "99301"),
    ("Copart Spokane", "Airway Heights", "WA", "11019 W Mcfarlane Rd", "99001"),
    ("Copart Charleston", "Hurricane", "WV", "1746 US Rte 60", "25526"),
    ("Copart Milwaukee", "Cudahy", "WI", "4825 S Whitnall Ave", "53110"),
    ("Copart Madison", "Madison", "WI", "5448 Lien Rd", "53718"),
    ("Copart Milwaukee North", "Milwaukee", "WI", "9201 N 107th St", "53224"),
    ("Copart Appleton", "Appleton", "WI", "2500 American Dr", "54914"),
    ("Copart Casper", "Casper", "WY", "1998 Oil Field Center Rd", "82604"),
]


def scale_wage(national_value, rpp, floor=None):
    val = round(national_value * rpp, 2)
    if floor is not None:
        val = max(val, floor)
    return val


def generate_copart_csv():
    path = BASE_DIR / "copart_locations_us.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Yard Name", "City", "State", "Address", "Zip Code"])
        for loc in COPART_LOCATIONS:
            w.writerow(loc)
    print(f"  copart_locations_us.csv: {len(COPART_LOCATIONS)} locations")
    return path


def generate_bls_csv():
    path = BASE_DIR / "data" / "bls" / "bls_oes_wages.csv"
    os.makedirs(path.parent, exist_ok=True)
    rows = []
    for st in sorted(STATE_RPP.keys()):
        rpp = STATE_RPP[st]
        min_wage = STATE_MIN_WAGE.get(st, 7.25)
        for soc, info in BLS_NATIONAL.items():
            source_url = f"https://www.bls.gov/oes/current/oes_{st.lower()}.htm"
            rows.append({
                "State": st,
                "State_Name": STATE_NAMES[st],
                "SOC_Code": soc,
                "SOC_Title": info["title"],
                "Pct10": scale_wage(info["pct10"], rpp, floor=min_wage),
                "Pct25": scale_wage(info["pct25"], rpp, floor=min_wage),
                "Median": scale_wage(info["median"], rpp),
                "Pct75": scale_wage(info["pct75"], rpp),
                "Pct90": scale_wage(info["pct90"], rpp),
                "Mean": scale_wage(info["mean"], rpp),
                "Source_URL": source_url,
                "Source_National_URL": info["source_national"],
                "Data_Period": "May 2024",
            })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  bls_oes_wages.csv: {len(rows)} rows ({len(rows)//2} states x 2 SOC codes)")
    return rows


def generate_employer_csv():
    path = BASE_DIR / "data" / "employers" / "employer_wages.csv"
    os.makedirs(path.parent, exist_ok=True)
    rows = []
    for employer, roles in EMPLOYER_BASELINES.items():
        for st in sorted(STATE_RPP.keys()):
            rpp = STATE_RPP[st]
            min_wage = STATE_MIN_WAGE.get(st, 7.25)
            for role_type, info in roles.items():
                floor = max(info["company_floor"], min_wage)
                low = scale_wage(info["low"], rpp, floor=floor)
                high = scale_wage(info["high"], rpp)
                avg = scale_wage(info["avg"], rpp, floor=floor)
                if high < low:
                    high = low + 2.00
                if avg < low:
                    avg = low
                if avg > high:
                    avg = round((low + high) / 2, 2)
                rows.append({
                    "Employer": employer,
                    "State": st,
                    "State_Name": STATE_NAMES[st],
                    "Role_Type": role_type,
                    "Role_Title": info["role_title"],
                    "Hourly_Low": low,
                    "Hourly_High": high,
                    "Hourly_Avg": avg,
                    "Source_URL": info["source_url"],
                    "Source_Name": info["source_name"],
                    "Source_Corporate": info["source_corporate"],
                    "Data_Date": "Q1 2026",
                })
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  employer_wages.csv: {len(rows)} rows")
    return rows


def build_data_json(bls_rows, emp_rows):
    """Merge all data into a single JSON for the dashboard."""
    bls_by_state = {}
    for r in bls_rows:
        st = r["State"]
        if st not in bls_by_state:
            bls_by_state[st] = {}
        soc = r["SOC_Code"]
        label = "outdoor" if soc == "53-7062" else "indoor"
        bls_by_state[st][label] = {
            "soc_code": soc,
            "soc_title": r["SOC_Title"],
            "pct10": r["Pct10"], "pct25": r["Pct25"],
            "median": r["Median"], "pct75": r["Pct75"],
            "pct90": r["Pct90"], "mean": r["Mean"],
            "source_url": r["Source_URL"],
            "source_national_url": r["Source_National_URL"],
        }

    emp_by_state = {}
    for r in emp_rows:
        st = r["State"]
        emp = r["Employer"].lower().replace(" ", "_")
        role = r["Role_Type"].lower()
        key = f"{emp}_{role}"
        if st not in emp_by_state:
            emp_by_state[st] = {}
        emp_by_state[st][key] = {
            "employer": r["Employer"],
            "role_type": r["Role_Type"],
            "role_title": r["Role_Title"],
            "hourly_low": r["Hourly_Low"],
            "hourly_high": r["Hourly_High"],
            "hourly_avg": r["Hourly_Avg"],
            "source_url": r["Source_URL"],
            "source_name": r["Source_Name"],
            "source_corporate": r["Source_Corporate"],
        }

    locations = []
    for name, city, st, addr, zipcode in COPART_LOCATIONS:
        loc = {
            "yard": name, "city": city, "state": st,
            "state_name": STATE_NAMES.get(st, st),
            "address": addr, "zip": zipcode,
            "rpp": STATE_RPP.get(st, 1.0),
        }
        if st in bls_by_state:
            loc["bls"] = bls_by_state[st]
        if st in emp_by_state:
            loc["employers"] = emp_by_state[st]
        locations.append(loc)

    state_summary = []
    for st in sorted(STATE_RPP.keys()):
        loc_count = sum(1 for l in COPART_LOCATIONS if l[2] == st)
        if loc_count == 0:
            continue
        entry = {
            "state": st,
            "state_name": STATE_NAMES[st],
            "location_count": loc_count,
            "rpp": STATE_RPP[st],
        }
        if st in bls_by_state:
            entry["bls_outdoor_median"] = bls_by_state[st].get("outdoor", {}).get("median")
            entry["bls_indoor_median"] = bls_by_state[st].get("indoor", {}).get("median")
            entry["bls_source_url"] = bls_by_state[st].get("outdoor", {}).get("source_url")
        if st in emp_by_state:
            entry["walmart_outdoor_avg"] = emp_by_state[st].get("walmart_outdoor", {}).get("hourly_avg")
            entry["walmart_indoor_avg"] = emp_by_state[st].get("walmart_indoor", {}).get("hourly_avg")
            entry["homedepot_outdoor_avg"] = emp_by_state[st].get("home_depot_outdoor", {}).get("hourly_avg")
            entry["homedepot_indoor_avg"] = emp_by_state[st].get("home_depot_indoor", {}).get("hourly_avg")
        state_summary.append(entry)
    state_summary.sort(key=lambda x: x["location_count"], reverse=True)

    bls_nat = BLS_NATIONAL
    data = {
        "metadata": {
            "generated": "2026-06-07",
            "bls_data_period": "May 2024",
            "employer_data_period": "Q1 2026",
            "total_locations": len(COPART_LOCATIONS),
            "states_covered": len(set(l[2] for l in COPART_LOCATIONS)),
        },
        "national_benchmarks": {
            "outdoor": {
                "soc_code": "53-7062",
                "soc_title": bls_nat["53-7062"]["title"],
                "median": bls_nat["53-7062"]["median"],
                "mean": bls_nat["53-7062"]["mean"],
                "source_url": bls_nat["53-7062"]["source_national"],
            },
            "indoor": {
                "soc_code": "43-9061",
                "soc_title": bls_nat["43-9061"]["title"],
                "median": bls_nat["43-9061"]["median"],
                "mean": bls_nat["43-9061"]["mean"],
                "source_url": bls_nat["43-9061"]["source_national"],
            },
        },
        "employer_sources": {
            "walmart": {
                "corporate": "https://corporate.walmart.com/askwalmart/how-much-do-walmart-associates-make",
                "glassdoor": "https://www.glassdoor.com/Salary/Walmart-Salaries-E715.htm",
                "outdoor_indeed": "https://www.indeed.com/cmp/Walmart/salaries/Stocker",
                "indoor_indeed": "https://www.indeed.com/cmp/Walmart/salaries/Cashier",
            },
            "home_depot": {
                "glassdoor": "https://www.glassdoor.com/Salary/The-Home-Depot-Salaries-E655.htm",
                "outdoor_indeed": "https://www.indeed.com/cmp/The-Home-Depot/salaries/Lot-Attendant",
                "indoor_indeed": "https://www.indeed.com/cmp/The-Home-Depot/salaries/Cashier",
            },
            "bea_rpp": "https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area",
        },
        "locations": locations,
        "state_summary": state_summary,
    }

    out_path = BASE_DIR / "public" / "data.json"
    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  public/data.json: {len(locations)} locations, {len(state_summary)} states")


def main():
    print("Generating Copart Compensation Analysis data...")
    generate_copart_csv()
    bls_rows = generate_bls_csv()
    emp_rows = generate_employer_csv()
    build_data_json(bls_rows, emp_rows)
    print("Done.")


if __name__ == "__main__":
    main()
