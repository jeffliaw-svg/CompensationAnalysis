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
  --q1: #1a365d;
  --q2: #2b6cb0;
  --q3: #ed8936;
  --q4: #e53e3e;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--slate);
  background: var(--gray-100);
  line-height: 1.5;
}
.container { max-width: 1600px; margin: 0 auto; padding: 0 24px; }
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
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}
.card {
  background: var(--white);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border-top: 3px solid var(--navy);
}
.card .label { font-size: 12px; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.card .value { font-size: 24px; font-weight: 700; color: var(--navy); }
.card .value a { color: var(--navy); text-decoration: none; border-bottom: 1px dashed var(--gray-500); }
.card .value a:hover { border-bottom-color: var(--navy); }
.card .detail { font-size: 12px; color: var(--slate); margin-top: 4px; }

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
.controls select { min-width: 140px; }
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
  padding: 10px 10px;
  text-align: left;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}
th:hover { background: var(--navy-light); }
th .sort-arrow { font-size: 10px; margin-left: 3px; opacity: 0.6; }
th.sorted .sort-arrow { opacity: 1; }
td { padding: 7px 10px; border-bottom: 1px solid var(--gray-200); }
tr:hover td { background: var(--gray-100); }
tr:nth-child(even) td { background: var(--gray-100); }
tr:nth-child(even):hover td { background: var(--gray-200); }

td a.wage-link {
  color: var(--blue-700);
  text-decoration: none;
  border-bottom: 1px dotted var(--gray-500);
  position: relative;
}
td a.wage-link:hover { color: var(--blue-600); border-bottom-style: solid; }
td.favorable { background: var(--green-50) !important; }
td.unfavorable { background: var(--red-50) !important; }
td.na-cell { color: var(--gray-500); font-style: italic; cursor: help; }
tr.subtotal-row td {
  background: var(--gray-200) !important;
  border-top: 2px solid var(--navy);
  border-bottom: 2px solid var(--navy);
  font-size: 12px;
  padding: 6px 10px;
}

.wage-cell { position: relative; }
.wage-cell .dist-tip {
  display: none;
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--navy);
  color: var(--white);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
  z-index: 10;
  pointer-events: none;
}
.wage-cell .dist-tip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--navy);
}
.wage-cell:hover .dist-tip { display: block; }

.q-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  color: var(--white);
}
.q-badge.q1 { background: var(--q1); }
.q-badge.q2 { background: var(--q2); }
.q-badge.q3 { background: var(--q3); }
.q-badge.q4 { background: var(--q4); }

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

.legend { display: flex; gap: 16px; margin-bottom: 12px; font-size: 12px; align-items: center; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }

.row-count { font-size: 13px; color: var(--gray-500); margin-bottom: 8px; }

@media (max-width: 1100px) {
  .charts-grid { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
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
    <div class="subtitle">BLS OES May 2024 Market Data &middot; Comparables: Walmart, Home Depot, Costco, Starbucks</div>
    <div class="meta">Generated {{ data.metadata.generated }} &middot; {{ data.metadata.total_locations }} locations across {{ data.metadata.states_covered }} states &middot; Ranked by inverse-distance weighted blended wage &middot; {{ data.metadata.distance_cutoff_mi|int }}-mile cutoff</div>
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
      <div class="label">BLS Median &mdash; Outdoor</div>
      <div class="value"><a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank" title="BLS OES: {{ data.national_benchmarks.outdoor.soc_title }}">${{ "%.2f"|format(data.national_benchmarks.outdoor.median) }}</a>/hr</div>
      <div class="detail">SOC {{ data.national_benchmarks.outdoor.soc_code }}</div>
    </div>
    <div class="card">
      <div class="label">BLS Median &mdash; Indoor</div>
      <div class="value"><a href="{{ data.national_benchmarks.indoor.source_url }}" target="_blank" title="BLS OES: {{ data.national_benchmarks.indoor.soc_title }}">${{ "%.2f"|format(data.national_benchmarks.indoor.median) }}</a>/hr</div>
      <div class="detail">SOC {{ data.national_benchmarks.indoor.soc_code }}</div>
    </div>
    <div class="card">
      <div class="label">Walmart (Outdoor)</div>
      <div class="value"><a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">{%- set wm_avg = [] %}{%- for s in data.state_summary %}{%- if s.walmart_outdoor %}{{ wm_avg.append(s.walmart_outdoor) or '' }}{%- endif %}{%- endfor %}${{ "%.2f"|format(wm_avg|sum / wm_avg|length) }}</a>/hr</div>
      <div class="detail">Stocking, national avg</div>
    </div>
    <div class="card">
      <div class="label">Home Depot (Outdoor)</div>
      <div class="value"><a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">{%- set hd_avg = [] %}{%- for s in data.state_summary %}{%- if s.homedepot_outdoor %}{{ hd_avg.append(s.homedepot_outdoor) or '' }}{%- endif %}{%- endfor %}${{ "%.2f"|format(hd_avg|sum / hd_avg|length) }}</a>/hr</div>
      <div class="detail">Lot Associate, national avg</div>
    </div>
    <div class="card">
      <div class="label">Costco (Outdoor)</div>
      <div class="value"><a href="{{ data.employer_sources.costco.outdoor_indeed }}" target="_blank">{%- set co_avg = [] %}{%- for s in data.state_summary %}{%- if s.costco_outdoor %}{{ co_avg.append(s.costco_outdoor) or '' }}{%- endif %}{%- endfor %}${{ "%.2f"|format(co_avg|sum / co_avg|length) }}</a>/hr</div>
      <div class="detail">Cart Attendant, national avg</div>
    </div>
    <div class="card">
      <div class="label">Starbucks (Outdoor)</div>
      <div class="value"><a href="{{ data.employer_sources.starbucks.outdoor_indeed }}" target="_blank">{%- set sb_avg = [] %}{%- for s in data.state_summary %}{%- if s.starbucks_outdoor %}{{ sb_avg.append(s.starbucks_outdoor) or '' }}{%- endif %}{%- endfor %}${{ "%.2f"|format(sb_avg|sum / sb_avg|length) }}</a>/hr</div>
      <div class="detail">Barista, national avg</div>
    </div>
  </div>

  <!-- Charts -->
  <div class="section">
    <h2 class="section-title">Wage Comparison by State (Top 15 by Copart Location Count)</h2>
    <div class="charts-grid">
      <div class="chart-card">
        <h3>Outdoor Roles: BLS Median vs. Employers</h3>
        <canvas id="chartOutdoor"></canvas>
      </div>
      <div class="chart-card">
        <h3>Indoor Roles: BLS Median vs. Employers</h3>
        <canvas id="chartIndoor"></canvas>
      </div>
    </div>
  </div>

  <!-- Tabs -->
  <div class="section">
    <h2 class="section-title">Detailed Compensation Data</h2>
    <div class="tab-row">
      <button class="tab-btn active" onclick="switchTab('locations')">All Locations (by Quartile)</button>
      <button class="tab-btn" onclick="switchTab('states')">State Summary</button>
    </div>

    <!-- Location Detail Tab -->
    <div id="tab-locations" class="tab-content active">
      <div class="controls">
        <input type="text" id="searchInput" placeholder="Search by yard name, city, or state..." oninput="filterTable()">
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
        <select id="quartileFilter" onchange="filterTable()">
          <option value="">All Quartiles</option>
          <option value="1">Q1 &mdash; Highest Wages</option>
          <option value="2">Q2</option>
          <option value="3">Q3</option>
          <option value="4">Q4 &mdash; Lowest Wages</option>
        </select>
      </div>
      <div class="legend">
        <span class="legend-item"><span class="legend-swatch" style="background:var(--green-50);border:1px solid var(--green-600)"></span> Below BLS median</span>
        <span class="legend-item"><span class="legend-swatch" style="background:var(--red-50);border:1px solid var(--red-600)"></span> Above BLS median</span>
        <span class="legend-item" style="margin-left:12px;"><span class="q-badge q1">Q1</span> Highest</span>
        <span class="legend-item"><span class="q-badge q2">Q2</span></span>
        <span class="legend-item"><span class="q-badge q3">Q3</span></span>
        <span class="legend-item"><span class="q-badge q4">Q4</span> Lowest</span>
      </div>
      <div class="row-count" id="rowCount"></div>
      <div class="table-wrap">
        <table id="locTable">
          <thead>
            <tr>
              <th data-col="quartile" onclick="sortTable('quartile')">Q <span class="sort-arrow">&#9650;</span></th>
              <th data-col="yard" onclick="sortTable('yard')">Yard Name <span class="sort-arrow">&#9650;</span></th>
              <th data-col="city" onclick="sortTable('city')">City <span class="sort-arrow">&#9650;</span></th>
              <th data-col="state" onclick="sortTable('state')">State <span class="sort-arrow">&#9650;</span></th>
              <th data-col="bls_median" onclick="sortTable('bls_median')">BLS Median <span class="sort-arrow">&#9650;</span></th>
              <th data-col="walmart" onclick="sortTable('walmart')">Walmart <span class="sort-arrow">&#9650;</span></th>
              <th data-col="homedepot" onclick="sortTable('homedepot')">Home Depot <span class="sort-arrow">&#9650;</span></th>
              <th data-col="costco" onclick="sortTable('costco')">Costco <span class="sort-arrow">&#9650;</span></th>
              <th data-col="starbucks" onclick="sortTable('starbucks')">Starbucks <span class="sort-arrow">&#9650;</span></th>
              <th data-col="blended" onclick="sortTable('blended')">Blended <span class="sort-arrow">&#9650;</span></th>
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
              <th>BLS Outdoor</th>
              <th>BLS Indoor</th>
              <th>Walmart</th>
              <th>Home Depot</th>
              <th>Costco</th>
              <th>Starbucks</th>
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
              <td>{% if s.walmart_outdoor %}<a class="wage-link" href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(s.walmart_outdoor) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.homedepot_outdoor %}<a class="wage-link" href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(s.homedepot_outdoor) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.costco_outdoor %}<a class="wage-link" href="{{ data.employer_sources.costco.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(s.costco_outdoor) }}</a>{% else %}&mdash;{% endif %}</td>
              <td>{% if s.starbucks_outdoor %}<a class="wage-link" href="{{ data.employer_sources.starbucks.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(s.starbucks_outdoor) }}</a>{% else %}&mdash;{% endif %}</td>
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
      <p>This analysis benchmarks the competitive wage environment for Copart operations roles against four comparable employers (Walmart, Home Depot, Costco, and Starbucks) and the BLS market baseline, across all {{ data.metadata.total_locations }} Copart US locations. Facilities are ranked by blended competitive wage and divided into quartiles (Q1 highest to Q4 lowest).</p>

      <h3>Role Mapping</h3>
      <table>
        <thead><tr><th>Employer</th><th>Outdoor Role Analog</th><th>Indoor Role Analog</th><th>Company Floor</th></tr></thead>
        <tbody>
          <tr><td>BLS OES</td><td><a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank">SOC 53-7062</a></td><td><a href="{{ data.national_benchmarks.indoor.source_url }}" target="_blank">SOC 43-9061</a></td><td>&mdash;</td></tr>
          <tr><td>Walmart</td><td><a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">Stocking/Unloading</a></td><td><a href="{{ data.employer_sources.walmart.indoor_indeed }}" target="_blank">Cashier</a></td><td>$14.00/hr</td></tr>
          <tr><td>Home Depot</td><td><a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">Lot Associate</a></td><td><a href="{{ data.employer_sources.home_depot.indoor_indeed }}" target="_blank">Cashier</a></td><td>$15.00/hr</td></tr>
          <tr><td>Costco</td><td><a href="{{ data.employer_sources.costco.outdoor_indeed }}" target="_blank">Cart Attendant</a></td><td><a href="{{ data.employer_sources.costco.indoor_indeed }}" target="_blank">Front End Assistant</a></td><td>$20.00/hr</td></tr>
          <tr><td>Starbucks</td><td><a href="{{ data.employer_sources.starbucks.outdoor_indeed }}" target="_blank">Barista</a></td><td><a href="{{ data.employer_sources.starbucks.indoor_indeed }}" target="_blank">Barista</a></td><td>$15.00/hr</td></tr>
        </tbody>
      </table>

      <h3>Data Sources</h3>
      <ul>
        <li><strong>BLS OES (May 2024):</strong> <a href="{{ data.national_benchmarks.outdoor.source_url }}" target="_blank">Occupational Employment and Wage Statistics</a>. National median adjusted to state level using BEA Regional Price Parities.</li>
        <li><strong>BEA Regional Price Parities (2023):</strong> <a href="{{ data.employer_sources.bea_rpp }}" target="_blank">Bureau of Economic Analysis</a>.</li>
        <li><strong>Walmart:</strong> <a href="{{ data.employer_sources.walmart.corporate }}" target="_blank">Corporate Disclosure</a>, <a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">Indeed</a>.</li>
        <li><strong>Home Depot:</strong> <a href="{{ data.employer_sources.home_depot.glassdoor }}" target="_blank">Glassdoor</a>, <a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">Indeed</a>.</li>
        <li><strong>Costco:</strong> <a href="{{ data.employer_sources.costco.corporate }}" target="_blank">Gridwise Pay Guide</a>, <a href="{{ data.employer_sources.costco.fortune }}" target="_blank">Fortune</a> (Teamsters agreement: $20/hr floor, rising to $22/hr by Mar 2027).</li>
        <li><strong>Starbucks:</strong> <a href="{{ data.employer_sources.starbucks.official }}" target="_blank">Starbucks Corporate</a>, <a href="{{ data.employer_sources.starbucks.corporate }}" target="_blank">Gridwise Pay Guide</a> ($15/hr floor, ~$17/hr avg).</li>
      </ul>

      <h3>Quartile Methodology</h3>
      <p>Facilities are ranked by <strong>blended competitive wage</strong>, computed as an inverse-distance weighted average of employer wages within {{ data.metadata.distance_cutoff_mi|int }} miles:</p>
      <p style="margin:8px 0;font-family:monospace;background:var(--gray-100);padding:8px 12px;border-radius:4px;">Blended = &Sigma;(wage<sub>i</sub> / dist<sub>i</sub>) / &Sigma;(1 / dist<sub>i</sub>)</p>
      <p>Competitors within {{ data.metadata.distance_cutoff_mi|int }} miles are weighted by 1/distance &mdash; a Walmart 2 miles away has 5&times; the weight of a Costco 10 miles away. Competitors beyond {{ data.metadata.distance_cutoff_mi|int }} miles are excluded and shown as N/A. The 197 locations are then divided into quartiles: Q1 (top 25%, highest competitive wages) through Q4 (bottom 25%, lowest). Q1 locations face the most competitive hiring environment.</p>

      <h3>Distance Estimates &amp; Cutoff</h3>
      <p>Hover over any employer wage cell to see the estimated distance to the nearest store. If a competitor&rsquo;s nearest store is more than <strong>{{ data.metadata.distance_cutoff_mi|int }} miles</strong> away, it is marked N/A and excluded from the blended score (hover the N/A to see actual distance). The {{ data.metadata.distance_cutoff_mi|int }}-mile cutoff reflects the practical commuting radius for hourly workers (BLS average commute: ~16 miles). Distances are estimated from metro classification and store density; they are directional, not GPS-measured.</p>

      <h3>Color Coding</h3>
      <ul>
        <li><span style="background:var(--green-50);padding:2px 8px;border:1px solid var(--green-600);border-radius:3px;">Green</span> &mdash; Employer wage is below BLS market median.</li>
        <li><span style="background:var(--red-50);padding:2px 8px;border:1px solid var(--red-600);border-radius:3px;">Red</span> &mdash; Employer wage is above BLS market median (competitive pressure).</li>
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
    <a href="{{ data.employer_sources.costco.corporate }}" target="_blank">Costco</a>,
    <a href="{{ data.employer_sources.starbucks.corporate }}" target="_blank">Starbucks</a>,
    <a href="{{ data.employer_sources.bea_rpp }}" target="_blank">BEA RPP</a>
  </div>
</footer>

<script>
const DATA = {{ data_json }};

const ROLE = { current: 'outdoor' };
let sortState = { col: 'blended', asc: false };

var CUTOFF = DATA.metadata.distance_cutoff_mi || 25;

function isInRange(loc, empKey) {
  return loc.in_range && loc.in_range[empKey];
}

function getVal(loc, field, role) {
  role = role || ROLE.current;
  var bls = loc.bls && loc.bls[role];
  var wm = loc.employers && loc.employers['walmart_' + role];
  var hd = loc.employers && loc.employers['home_depot_' + role];
  var co = loc.employers && loc.employers['costco_' + role];
  var sb = loc.employers && loc.employers['starbucks_' + role];
  switch(field) {
    case 'quartile': return loc.quartile;
    case 'yard': return loc.yard;
    case 'city': return loc.city;
    case 'state': return loc.state;
    case 'bls_median': return bls ? bls.median : null;
    case 'walmart': return (wm && isInRange(loc, 'walmart')) ? wm.hourly_avg : null;
    case 'homedepot': return (hd && isInRange(loc, 'home_depot')) ? hd.hourly_avg : null;
    case 'costco': return (co && isInRange(loc, 'costco')) ? co.hourly_avg : null;
    case 'starbucks': return (sb && isInRange(loc, 'starbucks')) ? sb.hourly_avg : null;
    case 'blended': return loc.blended_wage;
  }
}

function fmtWage(val, url, title) {
  if (val == null) return '&mdash;';
  return '<a class="wage-link" href="' + url + '" target="_blank" title="' + (title||'') + '">$' + val.toFixed(2) + '</a>';
}

function fmtWageWithDist(val, url, title, distMi) {
  if (val == null) return '';
  return '<a class="wage-link" href="' + url + '" target="_blank" title="' + (title||'') + '">$' + val.toFixed(2) + '</a>' +
    '<span class="dist-tip">Nearest: ' + distMi.toFixed(1) + ' mi</span>';
}

function cellClass(empVal, blsMedian) {
  if (empVal == null || blsMedian == null) return '';
  return empVal < blsMedian ? 'favorable' : empVal > blsMedian ? 'unfavorable' : '';
}

function renderTable() {
  var role = ROLE.current;
  var tbody = document.getElementById('locBody');
  var search = document.getElementById('searchInput').value.toLowerCase();
  var stateF = document.getElementById('stateFilter').value;
  var qF = document.getElementById('quartileFilter').value;

  var locs = DATA.locations.filter(function(l) {
    if (stateF && l.state !== stateF) return false;
    if (qF && l.quartile !== parseInt(qF)) return false;
    if (search && !(l.yard.toLowerCase().indexOf(search) >= 0 || l.city.toLowerCase().indexOf(search) >= 0 || l.state.toLowerCase().indexOf(search) >= 0 || l.state_name.toLowerCase().indexOf(search) >= 0)) return false;
    return true;
  });

  if (sortState.col) {
    locs.sort(function(a, b) {
      var va = getVal(a, sortState.col, role);
      var vb = getVal(b, sortState.col, role);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      return sortState.asc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
    });
  }

  var html = '';
  var qGroups = {};
  locs.forEach(function(loc, idx) {
    var bls = loc.bls && loc.bls[role];
    var wm = loc.employers && loc.employers['walmart_' + role];
    var hd = loc.employers && loc.employers['home_depot_' + role];
    var co = loc.employers && loc.employers['costco_' + role];
    var sb = loc.employers && loc.employers['starbucks_' + role];
    var blsUrl = bls ? bls.source_url : '#';
    var blsTitle = bls ? 'BLS OES ' + bls.soc_code + ' - ' + loc.state_name : '';
    var wmUrl = wm ? wm.source_url : '#';
    var hdUrl = hd ? hd.source_url : '#';
    var coUrl = co ? co.source_url : '#';
    var sbUrl = sb ? sb.source_url : '#';
    var blsMedian = bls ? bls.median : null;
    var dist = loc.nearest_distance_mi || {};
    var ir = loc.in_range || {};

    html += '<tr>';
    html += '<td><span class="q-badge q' + loc.quartile + '">Q' + loc.quartile + '</span></td>';
    html += '<td title="' + loc.address + ', ' + loc.city + ', ' + loc.state + ' ' + loc.zip + '"><strong>' + loc.yard + '</strong></td>';
    html += '<td>' + loc.city + '</td>';
    html += '<td>' + loc.state + '</td>';
    html += '<td>' + fmtWage(bls ? bls.median : null, blsUrl, blsTitle) + '</td>';

    // Walmart
    if (wm && ir.walmart) {
      html += '<td class="wage-cell ' + cellClass(wm.hourly_avg, blsMedian) + '">';
      html += fmtWageWithDist(wm.hourly_avg, wmUrl, wm.source_name, dist.walmart || 0);
      html += '</td>';
    } else {
      html += '<td class="na-cell" title="Nearest Walmart: ' + (dist.walmart || 0).toFixed(1) + ' mi (>' + CUTOFF + ' mi cutoff)">N/A</td>';
    }

    // Home Depot
    if (hd && ir.home_depot) {
      html += '<td class="wage-cell ' + cellClass(hd.hourly_avg, blsMedian) + '">';
      html += fmtWageWithDist(hd.hourly_avg, hdUrl, hd.source_name, dist.home_depot || 0);
      html += '</td>';
    } else {
      html += '<td class="na-cell" title="Nearest Home Depot: ' + (dist.home_depot || 0).toFixed(1) + ' mi (>' + CUTOFF + ' mi cutoff)">N/A</td>';
    }

    // Costco
    if (co && ir.costco) {
      html += '<td class="wage-cell ' + cellClass(co.hourly_avg, blsMedian) + '">';
      html += fmtWageWithDist(co.hourly_avg, coUrl, co.source_name, dist.costco || 0);
      html += '</td>';
    } else {
      html += '<td class="na-cell" title="Nearest Costco: ' + (dist.costco || 0).toFixed(1) + ' mi (>' + CUTOFF + ' mi cutoff)">N/A</td>';
    }

    // Starbucks
    if (sb && ir.starbucks) {
      html += '<td class="wage-cell ' + cellClass(sb.hourly_avg, blsMedian) + '">';
      html += fmtWageWithDist(sb.hourly_avg, sbUrl, sb.source_name, dist.starbucks || 0);
      html += '</td>';
    } else {
      html += '<td class="na-cell" title="Nearest Starbucks: ' + (dist.starbucks || 0).toFixed(1) + ' mi (>' + CUTOFF + ' mi cutoff)">N/A</td>';
    }

    html += '<td><strong>$' + loc.blended_wage.toFixed(2) + '</strong></td>';
    html += '</tr>';

    // Track for quartile subtotals
    if (!qGroups[loc.quartile]) qGroups[loc.quartile] = [];
    qGroups[loc.quartile].push(loc);

    // Insert subtotal row at quartile boundary
    var nextLoc = locs[idx + 1];
    if (!nextLoc || nextLoc.quartile !== loc.quartile) {
      var group = qGroups[loc.quartile];
      if (group && group.length > 0) {
        var qBlended = group.map(function(l) { return l.blended_wage; });
        var qMean = qBlended.reduce(function(a,b) { return a+b; }, 0) / qBlended.length;
        var sorted = qBlended.slice().sort(function(a,b) { return a-b; });
        var qMedian = sorted.length % 2 === 0
          ? (sorted[sorted.length/2-1] + sorted[sorted.length/2]) / 2
          : sorted[Math.floor(sorted.length/2)];
        html += '<tr class="subtotal-row">';
        html += '<td><span class="q-badge q' + loc.quartile + '">Q' + loc.quartile + '</span></td>';
        html += '<td colspan="3"><strong>Q' + loc.quartile + ' Subtotal</strong> (' + group.length + ' locations)</td>';
        html += '<td></td><td></td><td></td><td></td><td></td>';
        html += '<td><strong>Mean $' + qMean.toFixed(2) + ' / Med $' + qMedian.toFixed(2) + '</strong></td>';
        html += '</tr>';
      }
    }
  });
  tbody.innerHTML = html;
  document.getElementById('rowCount').textContent = locs.length + ' of ' + DATA.locations.length + ' locations';
}

function sortTable(col) {
  if (sortState.col === col) {
    sortState.asc = !sortState.asc;
  } else {
    sortState.col = col;
    sortState.asc = (col === 'yard' || col === 'city' || col === 'state');
  }
  document.querySelectorAll('#locTable th').forEach(function(th) {
    th.classList.remove('sorted');
    th.querySelector('.sort-arrow').textContent = '▲';
  });
  var th = document.querySelector('#locTable th[data-col="' + col + '"]');
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
  document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
  document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelector('.tab-btn[onclick*="' + tab + '"]').classList.add('active');
}

function buildCharts() {
  var top15 = DATA.state_summary.slice(0, 15);
  var labels = top15.map(function(s) { return s.state; });

  new Chart(document.getElementById('chartOutdoor'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'BLS Median', data: top15.map(function(s) { return s.bls_outdoor_median; }), backgroundColor: '#1a365d' },
        { label: 'Walmart', data: top15.map(function(s) { return s.walmart_outdoor; }), backgroundColor: '#2b6cb0' },
        { label: 'Home Depot', data: top15.map(function(s) { return s.homedepot_outdoor; }), backgroundColor: '#ed8936' },
        { label: 'Costco', data: top15.map(function(s) { return s.costco_outdoor; }), backgroundColor: '#38a169' },
        { label: 'Starbucks', data: top15.map(function(s) { return s.starbucks_outdoor; }), backgroundColor: '#805ad5' },
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
        { label: 'BLS Median', data: top15.map(function(s) { return s.bls_indoor_median; }), backgroundColor: '#1a365d' },
        { label: 'Walmart', data: top15.map(function(s) { return s.walmart_indoor; }), backgroundColor: '#2b6cb0' },
        { label: 'Home Depot', data: top15.map(function(s) { return s.homedepot_indoor; }), backgroundColor: '#ed8936' },
        { label: 'Costco', data: top15.map(function(s) { return s.costco_indoor; }), backgroundColor: '#38a169' },
        { label: 'Starbucks', data: top15.map(function(s) { return s.starbucks_indoor; }), backgroundColor: '#805ad5' },
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { beginAtZero: false, title: { display: true, text: '$/hr' } } }
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
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
