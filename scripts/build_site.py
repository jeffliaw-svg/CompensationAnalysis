#!/usr/bin/env python3
"""
Build the static HTML dashboard from public/data.json.
Produces public/index.html - a self-contained interactive dashboard.
"""

import json
from pathlib import Path
from jinja2 import Template

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Copart Compensation Analysis</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root {
  --navy: #1a365d;
  --navy-light: #2a4a7f;
  --slate: #4a5568;
  --gray-100: #f7fafc;
  --gray-200: #edf2f7;
  --gray-300: #e2e8f0;
  --gray-500: #a0aec0;
  --white: #ffffff;
  --green-50: #f0fff4;
  --green-600: #38a169;
  --red-50: #fff5f5;
  --red-600: #e53e3e;
  --blue-600: #2b6cb0;
  --blue-700: #2c5282;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--slate);
  background: var(--gray-100);
  line-height: 1.5;
}
.container { max-width: 1440px; margin: 0 auto; padding: 0 24px; }
header {
  background: var(--navy);
  color: var(--white);
  padding: 32px 0;
  margin-bottom: 32px;
}
header h1 { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
header .subtitle { font-size: 15px; opacity: 0.85; }
header .meta { font-size: 13px; opacity: 0.65; margin-top: 8px; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 36px;
}
.card {
  background: var(--white);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border-top: 3px solid var(--navy);
}
.card .label { font-size: 13px; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.card .value { font-size: 28px; font-weight: 700; color: var(--navy); }
.card .value a { color: var(--navy); text-decoration: none; border-bottom: 1px dashed var(--gray-500); }
.card .value a:hover { border-bottom-color: var(--navy); }
.card .detail { font-size: 13px; color: var(--slate); margin-top: 6px; }

.section { margin-bottom: 40px; }
.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--gray-200);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 36px;
}
.chart-card {
  background: var(--white);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.chart-card h3 { font-size: 15px; font-weight: 600; color: var(--navy); margin-bottom: 12px; }

.controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}
.controls input, .controls select {
  padding: 8px 12px;
  border: 1px solid var(--gray-300);
  border-radius: 6px;
  font-size: 14px;
  background: var(--white);
}
.controls input { flex: 1; min-width: 200px; max-width: 360px; }
.controls select { min-width: 160px; }
.controls label { font-size: 13px; color: var(--slate); font-weight: 500; }

.table-wrap {
  background: var(--white);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead { background: var(--navy); color: var(--white); position: sticky; top: 0; z-index: 2; }
th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}
th:hover { background: var(--navy-light); }
th .sort-arrow { font-size: 10px; margin-left: 4px; opacity: 0.6; }
th.sorted .sort-arrow { opacity: 1; }
td { padding: 8px 12px; border-bottom: 1px solid var(--gray-200); }
tr:hover td { background: var(--gray-100); }
tr:nth-child(even) td { background: var(--gray-100); }
tr:nth-child(even):hover td { background: var(--gray-200); }

td a.wage-link {
  color: var(--blue-700);
  text-decoration: none;
  border-bottom: 1px dotted var(--gray-500);
}
td a.wage-link:hover { color: var(--blue-600); border-bottom-style: solid; }
td.favorable { background: var(--green-50) !important; }
td.unfavorable { background: var(--red-50) !important; }

.methodology {
  background: var(--white);
  border-radius: 8px;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  font-size: 14px;
  line-height: 1.7;
}
.methodology h3 { font-size: 16px; font-weight: 600; color: var(--navy); margin: 20px 0 8px; }
.methodology h3:first-child { margin-top: 0; }
.methodology a { color: var(--blue-600); }
.methodology ul { margin-left: 20px; margin-bottom: 12px; }
.methodology li { margin-bottom: 4px; }
.methodology table { font-size: 13px; margin: 12px 0; }
.methodology td, .methodology th { padding: 6px 12px; border: 1px solid var(--gray-300); text-align: left; }
.methodology thead { background: var(--gray-200); color: var(--slate); position: static; }
.methodology th { color: var(--slate); cursor: default; }
.methodology th:hover { background: var(--gray-200); }

.tab-row {
  display: flex;
  border-bottom: 2px solid var(--gray-200);
  margin-bottom: 16px;
  gap: 0;
}
.tab-btn {
  padding: 10px 20px;
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-500);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}
.tab-btn.active { color: var(--navy); border-bottom-color: var(--navy); }
.tab-content { display: none; }
.tab-content.active { display: block; }

footer {
  text-align: center;
  padding: 32px 0;
  font-size: 12px;
  color: var(--gray-500);
}
footer a { color: var(--blue-600); }

.legend { display: flex; gap: 16px; margin-bottom: 12px; font-size: 12px; align-items: center; }
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }

.row-count { font-size: 13px; color: var(--gray-500); margin-bottom: 8px; }

@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
  .cards { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px) {
  .cards { grid-template-columns: 1fr; }
  header h1 { font-size: 22px; }
}
@media print {
  header { padding: 16px 0; }
  .controls, .tab-row { display: none; }
  .chart-card { break-inside: avoid; }
  .table-wrap { box-shadow: none; }
}
</style>
</head>
<body>

<header>
  <div class="container">
    <h1>Copart Compensation Analysis: Competitive Wage Landscape</h1>
    <div class="subtitle">BLS OES May 2024 Market Data &middot; Tier 1 Comparables: Walmart, Home Depot</div>
    <div class="meta">Generated {{ data.metadata.generated }} &middot; {{ data.metadata.total_locations }} locations across {{ data.metadata.states_covered }} states</div>
  </div>
</header>

<div class="container">

  <!-- Summary Cards -->
  <div class="cards">
    <div class="card">
      <div class="label">Copart Locations</div>
      <div class="value">{{ data.metadata.total_locations }}</div>
      <div class="detail">Across {{ data.metadata.states_covered }} states</div>
    </div>
    <div class="card">
      <div class="label">Market Median &mdash; Outdoor</div>
      <div class="value"><a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank" title="BLS OES: {{ data.national_benchmarks.outdoor.soc_title }}">${{ "%.2f"|format(data.national_benchmarks.outdoor.median) }}</a>/hr</div>
      <div class="detail">SOC {{ data.national_benchmarks.outdoor.soc_code }}</div>
    </div>
    <div class="card">
      <div class="label">Market Median &mdash; Indoor</div>
      <div class="value"><a href="{{ data.national_benchmarks.indoor.source_url }}" target="_blank" title="BLS OES: {{ data.national_benchmarks.indoor.soc_title }}">${{ "%.2f"|format(data.national_benchmarks.indoor.median) }}</a>/hr</div>
      <div class="detail">SOC {{ data.national_benchmarks.indoor.soc_code }}</div>
    </div>
    <div class="card">
      <div class="label">Walmart Avg (Outdoor)</div>
      <div class="value"><a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank" title="Indeed: Walmart Stocker salaries">${% set wm_avg = [] %}{%- for s in data.state_summary %}{%- if s.walmart_outdoor_avg %}{{ wm_avg.append(s.walmart_outdoor_avg) or '' }}{%- endif %}{%- endfor %}{{ "%.2f"|format(wm_avg|sum / wm_avg|length) }}</a>/hr</div>
      <div class="detail">Stocking/Unloading, national avg</div>
    </div>
    <div class="card">
      <div class="label">Home Depot Avg (Outdoor)</div>
      <div class="value"><a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank" title="Indeed: Home Depot Lot Attendant salaries">{%- set hd_avg = [] %}{%- for s in data.state_summary %}{%- if s.homedepot_outdoor_avg %}{{ hd_avg.append(s.homedepot_outdoor_avg) or '' }}{%- endif %}{%- endfor %}${{ "%.2f"|format(hd_avg|sum / hd_avg|length) }}</a>/hr</div>
      <div class="detail">Lot/Receiving Associate, national avg</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="section">
    <h2 class="section-title">Wage Comparison by State (Top 15 by Copart Location Count)</h2>
    <div class="charts-grid">
      <div class="chart-card">
        <h3>Outdoor Roles: BLS Market Median vs. Employer Averages</h3>
        <canvas id="chartOutdoor"></canvas>
      </div>
      <div class="chart-card">
        <h3>Indoor Roles: BLS Market Median vs. Employer Averages</h3>
        <canvas id="chartIndoor"></canvas>
      </div>
    </div>
  </div>

  <!-- Tabs: Location Detail / State Summary -->
  <div class="section">
    <h2 class="section-title">Detailed Compensation Data</h2>
    <div class="tab-row">
      <button class="tab-btn active" onclick="switchTab('locations')">All Locations</button>
      <button class="tab-btn" onclick="switchTab('states')">State Summary</button>
    </div>

    <!-- Location Detail Tab -->
    <div id="tab-locations" class="tab-content active">
      <div class="controls">
        <input type="text" id="searchInput" placeholder="Search by yard name or city..." oninput="filterTable()">
        <select id="stateFilter" onchange="filterTable()">
          <option value="">All States</option>
          {%- for s in data.state_summary %}
          <option value="{{ s.state }}">{{ s.state }} - {{ s.state_name }} ({{ s.location_count }})</option>
          {%- endfor %}
        </select>
        <select id="roleFilter" onchange="switchRole()">
          <option value="outdoor">Outdoor Roles</option>
          <option value="indoor">Indoor Roles</option>
        </select>
      </div>
      <div class="legend">
        <span class="legend-item"><span class="legend-swatch" style="background:var(--green-50);border:1px solid var(--green-600)"></span> Employer below BLS median (favorable)</span>
        <span class="legend-item"><span class="legend-swatch" style="background:var(--red-50);border:1px solid var(--red-600)"></span> Employer above BLS median (competitive pressure)</span>
      </div>
      <div class="row-count" id="rowCount"></div>
      <div class="table-wrap">
        <table id="locTable">
          <thead>
            <tr>
              <th data-col="yard" onclick="sortTable('yard')">Yard Name <span class="sort-arrow">&#9650;</span></th>
              <th data-col="city" onclick="sortTable('city')">City <span class="sort-arrow">&#9650;</span></th>
              <th data-col="state" onclick="sortTable('state')">State <span class="sort-arrow">&#9650;</span></th>
              <th data-col="bls_median" onclick="sortTable('bls_median')">BLS Median <span class="sort-arrow">&#9650;</span></th>
              <th data-col="bls_p25" onclick="sortTable('bls_p25')">BLS P25 <span class="sort-arrow">&#9650;</span></th>
              <th data-col="bls_p75" onclick="sortTable('bls_p75')">BLS P75 <span class="sort-arrow">&#9650;</span></th>
              <th data-col="walmart" onclick="sortTable('walmart')">Walmart Avg <span class="sort-arrow">&#9650;</span></th>
              <th data-col="homedepot" onclick="sortTable('homedepot')">Home Depot Avg <span class="sort-arrow">&#9650;</span></th>
              <th data-col="rpp" onclick="sortTable('rpp')">RPP <span class="sort-arrow">&#9650;</span></th>
            </tr>
          </thead>
          <tbody id="locBody"></tbody>
        </table>
      </div>
    </div>

    <!-- State Summary Tab -->
    <div id="tab-states" class="tab-content">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>State</th>
              <th>Locations</th>
              <th>RPP</th>
              <th>BLS Outdoor Median</th>
              <th>BLS Indoor Median</th>
              <th>Walmart Outdoor</th>
              <th>Walmart Indoor</th>
              <th>Home Depot Outdoor</th>
              <th>Home Depot Indoor</th>
            </tr>
          </thead>
          <tbody>
            {%- for s in data.state_summary %}
            <tr>
              <td><strong>{{ s.state }}</strong> &ndash; {{ s.state_name }}</td>
              <td>{{ s.location_count }}</td>
              <td>{{ "%.3f"|format(s.rpp) }}</td>
              <td>{% if s.bls_outdoor_median %}<a class="wage-link" href="{{ s.bls_source_url }}" target="_blank">${{ "%.2f"|format(s.bls_outdoor_median) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.bls_indoor_median %}<a class="wage-link" href="{{ s.bls_source_url }}" target="_blank">${{ "%.2f"|format(s.bls_indoor_median) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.walmart_outdoor_avg %}<a class="wage-link" href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(s.walmart_outdoor_avg) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.walmart_indoor_avg %}<a class="wage-link" href="{{ data.employer_sources.walmart.indoor_indeed }}" target="_blank">${{ "%.2f"|format(s.walmart_indoor_avg) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.homedepot_outdoor_avg %}<a class="wage-link" href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(s.homedepot_outdoor_avg) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.homedepot_indoor_avg %}<a class="wage-link" href="{{ data.employer_sources.home_depot.indoor_indeed }}" target="_blank">${{ "%.2f"|format(s.homedepot_indoor_avg) }}</a>{% else %}&mdash;{% endif %}</td>
            </tr>
            {%- endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Methodology -->
  <div class="section" id="methodology">
    <h2 class="section-title">Methodology &amp; Sources</h2>
    <div class="methodology">

      <h3>Overview</h3>
      <p>This analysis benchmarks the competitive wage environment for Copart operations roles against two Tier 1 comparable employers (Walmart and Home Depot) and the BLS market baseline, across all {{ data.metadata.total_locations }} Copart US locations.</p>

      <h3>Role Mapping</h3>
      <table>
        <thead><tr><th>Tier</th><th>Employer</th><th>Outdoor Role Analog</th><th>Indoor Role Analog</th></tr></thead>
        <tbody>
          <tr><td>Baseline</td><td>BLS OES</td><td><a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank">SOC 53-7062: {{ data.national_benchmarks.outdoor.soc_title }}</a></td><td><a href="{{ data.national_benchmarks.indoor.source_url }}" target="_blank">SOC 43-9061: {{ data.national_benchmarks.indoor.soc_title }}</a></td></tr>
          <tr><td>Tier 1</td><td>Walmart</td><td><a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">Stocking/Unloading Associate</a></td><td><a href="{{ data.employer_sources.walmart.indoor_indeed }}" target="_blank">Cashier/Customer Service</a></td></tr>
          <tr><td>Tier 1</td><td>Home Depot</td><td><a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">Lot Associate / Receiving</a></td><td><a href="{{ data.employer_sources.home_depot.indoor_indeed }}" target="_blank">Cashier/Customer Service</a></td></tr>
        </tbody>
      </table>

      <h3>Data Sources</h3>
      <ul>
        <li><strong>BLS OES (May 2024):</strong> <a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank">Occupational Employment and Wage Statistics</a>. National percentile benchmarks adjusted to state level using BEA Regional Price Parities.</li>
        <li><strong>BEA Regional Price Parities (2023):</strong> <a href="{{ data.employer_sources.bea_rpp }}" target="_blank">Bureau of Economic Analysis</a>. State-level price indices used to scale national wage benchmarks to reflect local cost-of-living differences.</li>
        <li><strong>Walmart wages:</strong> <a href="{{ data.employer_sources.walmart.corporate }}" target="_blank">Walmart Corporate Disclosure</a>, <a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">Indeed Stocker Salaries</a>, <a href="{{ data.employer_sources.walmart.indoor_indeed }}" target="_blank">Indeed Cashier Salaries</a>, <a href="{{ data.employer_sources.walmart.glassdoor }}" target="_blank">Glassdoor</a>.</li>
        <li><strong>Home Depot wages:</strong> <a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">Indeed Lot Attendant Salaries</a>, <a href="{{ data.employer_sources.home_depot.indoor_indeed }}" target="_blank">Indeed Cashier Salaries</a>, <a href="{{ data.employer_sources.home_depot.glassdoor }}" target="_blank">Glassdoor</a>.</li>
      </ul>

      <h3>State-Level Adjustment Methodology</h3>
      <p>National wage benchmarks are adjusted to each state using the formula: <code>State Wage = National Wage &times; (State RPP / National RPP)</code>. RPP (Regional Price Parity) values from the BEA measure price-level differences across states. This provides a consistent, defensible mechanism for estimating state-level wages from nationally verified benchmarks.</p>
      <p>State minimum wage floors are applied: no estimated wage falls below the applicable state or federal minimum wage.</p>

      <h3>Employer Minimum Wage Floors</h3>
      <ul>
        <li>Walmart company-wide minimum: $14.00/hr (applied globally)</li>
        <li>Home Depot company-wide minimum: $15.00/hr (since February 2023)</li>
        <li>State minimum wages override employer floors where higher</li>
      </ul>

      <h3>Color Coding</h3>
      <ul>
        <li><span style="background:var(--green-50);padding:2px 8px;border:1px solid var(--green-600);border-radius:3px;">Green</span> &mdash; Employer average is <em>below</em> BLS market median. Indicates Copart is more competitive relative to this employer in this market.</li>
        <li><span style="background:var(--red-50);padding:2px 8px;border:1px solid var(--red-600);border-radius:3px;">Red</span> &mdash; Employer average is <em>above</em> BLS market median. Indicates competitive pressure from this employer.</li>
      </ul>

      <h3>Limitations</h3>
      <ul>
        <li>BLS OES data reflects the May 2024 survey period (most recent available). Employer data reflects Q1 2026 aggregated salary reports.</li>
        <li>State-level employer wages are estimated from national averages scaled by RPP, not from individual store-level postings. Actual wages may vary by metro area.</li>
        <li>This analysis does not include benefits, shift differentials, or non-wage compensation.</li>
        <li>Distance to nearest competitor location is not yet incorporated (future enhancement).</li>
      </ul>

    </div>
  </div>

</div>

<footer>
  <div class="container">
    Copart Compensation Analysis &middot; Generated {{ data.metadata.generated }} &middot;
    Data: <a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank">BLS OES</a>,
    <a href="{{ data.employer_sources.walmart.corporate }}" target="_blank">Walmart</a>,
    <a href="{{ data.employer_sources.home_depot.glassdoor }}" target="_blank">Home Depot</a>,
    <a href="{{ data.employer_sources.bea_rpp }}" target="_blank">BEA RPP</a>
  </div>
</footer>

<script>
const DATA = {{ data_json }};

const ROLE = { current: 'outdoor' };
let sortState = { col: null, asc: true };

function getVal(loc, field, role) {
  role = role || ROLE.current;
  const bls = loc.bls && loc.bls[role];
  const wm = loc.employers && loc.employers['walmart_' + role];
  const hd = loc.employers && loc.employers['home_depot_' + role];
  switch(field) {
    case 'yard': return loc.yard;
    case 'city': return loc.city;
    case 'state': return loc.state;
    case 'bls_median': return bls ? bls.median : null;
    case 'bls_p25': return bls ? bls.pct25 : null;
    case 'bls_p75': return bls ? bls.pct75 : null;
    case 'walmart': return wm ? wm.hourly_avg : null;
    case 'homedepot': return hd ? hd.hourly_avg : null;
    case 'rpp': return loc.rpp;
  }
}

function fmtWage(val, url, title) {
  if (val == null) return '&mdash;';
  return '<a class="wage-link" href="' + url + '" target="_blank" title="' + (title||'') + '">$' + val.toFixed(2) + '</a>';
}

function cellClass(empVal, blsMedian) {
  if (empVal == null || blsMedian == null) return '';
  return empVal < blsMedian ? 'favorable' : empVal > blsMedian ? 'unfavorable' : '';
}

function renderTable() {
  const role = ROLE.current;
  const tbody = document.getElementById('locBody');
  const search = document.getElementById('searchInput').value.toLowerCase();
  const stateF = document.getElementById('stateFilter').value;

  let locs = DATA.locations.filter(l => {
    if (stateF && l.state !== stateF) return false;
    if (search && !(l.yard.toLowerCase().includes(search) || l.city.toLowerCase().includes(search) || l.state.toLowerCase().includes(search))) return false;
    return true;
  });

  if (sortState.col) {
    locs.sort((a, b) => {
      let va = getVal(a, sortState.col, role);
      let vb = getVal(b, sortState.col, role);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      return sortState.asc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
    });
  }

  let html = '';
  locs.forEach(loc => {
    const bls = loc.bls && loc.bls[role];
    const wm = loc.employers && loc.employers['walmart_' + role];
    const hd = loc.employers && loc.employers['home_depot_' + role];
    const blsUrl = bls ? bls.source_url : '#';
    const blsTitle = bls ? 'BLS OES ' + bls.soc_code + ' - ' + loc.state_name : '';
    const wmUrl = wm ? wm.source_url : '#';
    const hdUrl = hd ? hd.source_url : '#';
    const blsMedian = bls ? bls.median : null;

    html += '<tr>';
    html += '<td><strong>' + loc.yard + '</strong></td>';
    html += '<td>' + loc.city + '</td>';
    html += '<td>' + loc.state + '</td>';
    html += '<td>' + fmtWage(bls ? bls.median : null, blsUrl, blsTitle) + '</td>';
    html += '<td>' + fmtWage(bls ? bls.pct25 : null, blsUrl, blsTitle) + '</td>';
    html += '<td>' + fmtWage(bls ? bls.pct75 : null, blsUrl, blsTitle) + '</td>';
    html += '<td class="' + cellClass(wm ? wm.hourly_avg : null, blsMedian) + '">' + fmtWage(wm ? wm.hourly_avg : null, wmUrl, wm ? wm.source_name : '') + '</td>';
    html += '<td class="' + cellClass(hd ? hd.hourly_avg : null, blsMedian) + '">' + fmtWage(hd ? hd.hourly_avg : null, hdUrl, hd ? hd.source_name : '') + '</td>';
    html += '<td>' + loc.rpp.toFixed(3) + '</td>';
    html += '</tr>';
  });
  tbody.innerHTML = html;
  document.getElementById('rowCount').textContent = locs.length + ' of ' + DATA.locations.length + ' locations';
}

function sortTable(col) {
  if (sortState.col === col) {
    sortState.asc = !sortState.asc;
  } else {
    sortState.col = col;
    sortState.asc = true;
  }
  document.querySelectorAll('#locTable th').forEach(th => {
    th.classList.remove('sorted');
    th.querySelector('.sort-arrow').textContent = '▲';
  });
  const th = document.querySelector('#locTable th[data-col="' + col + '"]');
  if (th) {
    th.classList.add('sorted');
    th.querySelector('.sort-arrow').textContent = sortState.asc ? '▲' : '▼';
  }
  renderTable();
}

function filterTable() { renderTable(); }
function switchRole() {
  ROLE.current = document.getElementById('roleFilter').value;
  renderTable();
}

function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelector('.tab-btn[onclick*="' + tab + '"]').classList.add('active');
}

// Charts
function buildCharts() {
  const top15 = DATA.state_summary.slice(0, 15);
  const labels = top15.map(s => s.state);

  new Chart(document.getElementById('chartOutdoor'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'BLS Median', data: top15.map(s => s.bls_outdoor_median), backgroundColor: '#1a365d' },
        { label: 'Walmart Avg', data: top15.map(s => s.walmart_outdoor_avg), backgroundColor: '#2b6cb0' },
        { label: 'Home Depot Avg', data: top15.map(s => s.homedepot_outdoor_avg), backgroundColor: '#ed8936' },
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { beginAtZero: false, title: { display: true, text: '$/hr' } } }
    }
  });

  new Chart(document.getElementById('chartIndoor'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'BLS Median', data: top15.map(s => s.bls_indoor_median), backgroundColor: '#1a365d' },
        { label: 'Walmart Avg', data: top15.map(s => s.walmart_indoor_avg), backgroundColor: '#2b6cb0' },
        { label: 'Home Depot Avg', data: top15.map(s => s.homedepot_indoor_avg), backgroundColor: '#ed8936' },
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { beginAtZero: false, title: { display: true, text: '$/hr' } } }
    }
  });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  renderTable();
  buildCharts();
});
</script>
</body>
</html>
"""


def main():
    data_path = BASE_DIR / "public" / "data.json"
    with open(data_path) as f:
        data = json.load(f)

    data_json_str = json.dumps(data)

    template = Template(TEMPLATE)
    html = template.render(data=data, data_json=data_json_str)

    out_path = BASE_DIR / "public" / "index.html"
    with open(out_path, "w") as f:
        f.write(html)

    print(f"Dashboard built: {out_path}")
    print(f"  {data['metadata']['total_locations']} locations, {data['metadata']['states_covered']} states")


if __name__ == "__main__":
    main()
