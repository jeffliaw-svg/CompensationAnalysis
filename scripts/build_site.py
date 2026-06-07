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

.toggle-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 12px 20px;
  background: var(--white);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.toggle-bar label { font-size: 14px; font-weight: 600; color: var(--navy); }
.toggle-switch {
  position: relative;
  width: 48px;
  height: 26px;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--navy);
  border-radius: 26px;
  transition: 0.3s;
}
.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  bottom: 3px;
  background: var(--white);
  border-radius: 50%;
  transition: 0.3s;
}
.toggle-switch input:checked + .toggle-slider { background: var(--q3); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(22px); }
.toggle-label { font-size: 14px; color: var(--slate); font-weight: 500; min-width: 60px; }
.toggle-label.active { color: var(--navy); font-weight: 700; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
.card-wages { margin: 4px 0; }
.card-wage-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 2px; }
.card-role { font-size: 12px; color: var(--gray-500); min-width: 52px; }
.card-amt { font-size: 22px; font-weight: 700; color: var(--navy); text-decoration: none; border-bottom: 1px dashed var(--gray-500); }
.card-amt:hover { border-bottom-color: var(--navy); }

.section { margin-bottom: 40px; }
.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--navy);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--gray-200);
}

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

.yard-addr { font-size: 11px; color: var(--gray-500); font-weight: 400; white-space: nowrap; }
td a.wage-link {
  color: var(--blue-700);
  text-decoration: none;
  border-bottom: 1px dotted var(--gray-500);
}
td a.wage-link:hover { color: var(--blue-600); border-bottom-style: solid; }
td.na-cell { color: var(--gray-500); font-style: italic; cursor: help; }

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
  white-space: normal;
  width: 180px;
  text-align: center;
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

tr.q-first td { border-top: 3px solid var(--navy); }
tr.subtotal-row td {
  background: var(--gray-200) !important;
  font-size: 12px;
  padding: 5px 10px;
  font-weight: 600;
}
tr.subtotal-row.mean-row td { border-top: 2px solid var(--gray-300); }
tr.subtotal-row.median-row td { border-bottom: none; }
tr.q-spacer td {
  background: var(--gray-100) !important;
  border: none;
  height: 16px;
  padding: 0;
}

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

.row-count { font-size: 13px; color: var(--gray-500); margin-bottom: 8px; }

@media (max-width: 900px) {
  .cards { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 600px) {
  .cards { grid-template-columns: 1fr; }
  header h1 { font-size: 22px; }
}
@media print {
  header { padding: 16px 0; }
  .controls, .tab-row, .toggle-bar { display: none; }
  .table-wrap { box-shadow: none; }
}
</style>
</head>
<body>

<header>
  <div class="container">
    <h1>Copart Compensation Analysis: Competitive Wage Landscape</h1>
    <div class="subtitle">Comparables: Walmart, Home Depot, Costco, Starbucks</div>
    <div class="meta">Generated {{ data.metadata.generated }} &middot; {{ data.metadata.total_locations }} locations across {{ data.metadata.states_covered }} states &middot; Ranked by inverse-distance weighted blended wage &middot; {{ data.metadata.distance_cutoff_mi|int }}-mile cutoff</div>
  </div>
</header>

<div class="container">

  <!-- Indoor/Outdoor Toggle -->
  <div class="toggle-bar">
    <label>Role Type:</label>
    <span class="toggle-label active" id="lbl-outdoor">Outdoor</span>
    <label class="toggle-switch">
      <input type="checkbox" id="roleToggle" onchange="switchRole()">
      <span class="toggle-slider"></span>
    </label>
    <span class="toggle-label" id="lbl-indoor">Indoor</span>
  </div>

  <!-- Summary Cards -->
  <div class="cards">
    <div class="card">
      <div class="label">Locations</div>
      <div class="value">{{ data.metadata.total_locations }}</div>
      <div class="detail">Across {{ data.metadata.states_covered }} states</div>
    </div>
    <div class="card">
      <div class="label">Walmart</div>
      {%- set wm_out = [] %}{%- set wm_in = [] %}{%- for s in data.state_summary %}{%- if s.walmart_outdoor %}{{ wm_out.append(s.walmart_outdoor) or '' }}{%- endif %}{%- if s.walmart_indoor %}{{ wm_in.append(s.walmart_indoor) or '' }}{%- endif %}{%- endfor %}
      <div class="card-wages">
        <div class="card-wage-row"><span class="card-role">Outdoor</span> <a class="card-amt" href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(wm_out|sum / wm_out|length) }}/hr</a></div>
        <div class="card-wage-row"><span class="card-role">Indoor</span> <a class="card-amt" href="{{ data.employer_sources.walmart.indoor_indeed }}" target="_blank">${{ "%.2f"|format(wm_in|sum / wm_in|length) }}/hr</a></div>
      </div>
      <div class="detail">National avg</div>
    </div>
    <div class="card">
      <div class="label">Home Depot</div>
      {%- set hd_out = [] %}{%- set hd_in = [] %}{%- for s in data.state_summary %}{%- if s.homedepot_outdoor %}{{ hd_out.append(s.homedepot_outdoor) or '' }}{%- endif %}{%- if s.homedepot_indoor %}{{ hd_in.append(s.homedepot_indoor) or '' }}{%- endif %}{%- endfor %}
      <div class="card-wages">
        <div class="card-wage-row"><span class="card-role">Outdoor</span> <a class="card-amt" href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(hd_out|sum / hd_out|length) }}/hr</a></div>
        <div class="card-wage-row"><span class="card-role">Indoor</span> <a class="card-amt" href="{{ data.employer_sources.home_depot.indoor_indeed }}" target="_blank">${{ "%.2f"|format(hd_in|sum / hd_in|length) }}/hr</a></div>
      </div>
      <div class="detail">National avg</div>
    </div>
    <div class="card">
      <div class="label">Costco</div>
      {%- set co_out = [] %}{%- set co_in = [] %}{%- for s in data.state_summary %}{%- if s.costco_outdoor %}{{ co_out.append(s.costco_outdoor) or '' }}{%- endif %}{%- if s.costco_indoor %}{{ co_in.append(s.costco_indoor) or '' }}{%- endif %}{%- endfor %}
      <div class="card-wages">
        <div class="card-wage-row"><span class="card-role">Outdoor</span> <a class="card-amt" href="{{ data.employer_sources.costco.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(co_out|sum / co_out|length) }}/hr</a></div>
        <div class="card-wage-row"><span class="card-role">Indoor</span> <a class="card-amt" href="{{ data.employer_sources.costco.indoor_indeed }}" target="_blank">${{ "%.2f"|format(co_in|sum / co_in|length) }}/hr</a></div>
      </div>
      <div class="detail">National avg</div>
    </div>
    <div class="card">
      <div class="label">Starbucks</div>
      {%- set sb_out = [] %}{%- set sb_in = [] %}{%- for s in data.state_summary %}{%- if s.starbucks_outdoor %}{{ sb_out.append(s.starbucks_outdoor) or '' }}{%- endif %}{%- if s.starbucks_indoor %}{{ sb_in.append(s.starbucks_indoor) or '' }}{%- endif %}{%- endfor %}
      <div class="card-wages">
        <div class="card-wage-row"><span class="card-role">Outdoor</span> <a class="card-amt" href="{{ data.employer_sources.starbucks.outdoor_indeed }}" target="_blank">${{ "%.2f"|format(sb_out|sum / sb_out|length) }}/hr</a></div>
        <div class="card-wage-row"><span class="card-role">Indoor</span> <a class="card-amt" href="{{ data.employer_sources.starbucks.indoor_indeed }}" target="_blank">${{ "%.2f"|format(sb_in|sum / sb_in|length) }}/hr</a></div>
      </div>
      <div class="detail">National avg</div>
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
        <select id="quartileFilter" onchange="filterTable()">
          <option value="">All Quartiles</option>
          <option value="1">Q1 &mdash; Highest Wages</option>
          <option value="2">Q2</option>
          <option value="3">Q3</option>
          <option value="4">Q4 &mdash; Lowest Wages</option>
        </select>
      </div>
      <div class="legend">
        <span class="legend-item"><span class="q-badge q1">Q1</span> Highest</span>
        <span class="legend-item"><span class="q-badge q2">Q2</span></span>
        <span class="legend-item"><span class="q-badge q3">Q3</span></span>
        <span class="legend-item"><span class="q-badge q4">Q4</span> Lowest</span>
        <span style="margin-left:8px;color:var(--gray-500)">Hover wage for nearest store distance &middot; Hover yard name for address</span>
      </div>
      <div class="row-count" id="rowCount"></div>
      <div class="table-wrap">
        <table id="locTable">
          <thead>
            <tr>
              <th data-col="quartile" onclick="sortTable('quartile')">Q <span class="sort-arrow">&#9650;</span></th>
              <th data-col="yard" onclick="sortTable('yard')">Yard Name <span class="sort-arrow">&#9650;</span></th>
              <th data-col="city" onclick="sortTable('city')">City, State <span class="sort-arrow">&#9650;</span></th>
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
      <p>This analysis benchmarks the competitive wage environment for Copart operations roles against four comparable employers (Walmart, Home Depot, Costco, and Starbucks) across all {{ data.metadata.total_locations }} Copart US locations. Facilities are ranked by blended competitive wage and divided into quartiles (Q1 highest to Q4 lowest).</p>

      <h3>Role Mapping</h3>
      <table>
        <thead><tr><th>Employer</th><th>Outdoor Role Analog</th><th>Indoor Role Analog</th><th>Company Floor</th></tr></thead>
        <tbody>
          <tr><td>Walmart</td><td><a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">Stocking/Unloading</a></td><td><a href="{{ data.employer_sources.walmart.indoor_indeed }}" target="_blank">Cashier</a></td><td>$14.00/hr</td></tr>
          <tr><td>Home Depot</td><td><a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">Lot Associate</a></td><td><a href="{{ data.employer_sources.home_depot.indoor_indeed }}" target="_blank">Cashier</a></td><td>$15.00/hr</td></tr>
          <tr><td>Costco</td><td><a href="{{ data.employer_sources.costco.outdoor_indeed }}" target="_blank">Cart Attendant</a></td><td><a href="{{ data.employer_sources.costco.indoor_indeed }}" target="_blank">Front End Assistant</a></td><td>$20.00/hr</td></tr>
          <tr><td>Starbucks</td><td><a href="{{ data.employer_sources.starbucks.outdoor_indeed }}" target="_blank">Barista</a></td><td><a href="{{ data.employer_sources.starbucks.indoor_indeed }}" target="_blank">Barista</a></td><td>$15.00/hr</td></tr>
        </tbody>
      </table>

      <h3>Data Sources</h3>
      <ul>
        <li><strong>BEA Regional Price Parities (2023):</strong> <a href="{{ data.employer_sources.bea_rpp }}" target="_blank">Bureau of Economic Analysis</a>. State-level price indices used to scale national employer wage benchmarks.</li>
        <li><strong>Walmart:</strong> <a href="{{ data.employer_sources.walmart.corporate }}" target="_blank">Corporate Disclosure</a>, <a href="{{ data.employer_sources.walmart.outdoor_indeed }}" target="_blank">Indeed</a>.</li>
        <li><strong>Home Depot:</strong> <a href="{{ data.employer_sources.home_depot.glassdoor }}" target="_blank">Glassdoor</a>, <a href="{{ data.employer_sources.home_depot.outdoor_indeed }}" target="_blank">Indeed</a>.</li>
        <li><strong>Costco:</strong> <a href="{{ data.employer_sources.costco.corporate }}" target="_blank">Gridwise Pay Guide</a>, <a href="{{ data.employer_sources.costco.fortune }}" target="_blank">Fortune</a> (Teamsters agreement: $20/hr floor, rising to $22/hr by Mar 2027).</li>
        <li><strong>Starbucks:</strong> <a href="{{ data.employer_sources.starbucks.official }}" target="_blank">Starbucks Corporate</a>, <a href="{{ data.employer_sources.starbucks.corporate }}" target="_blank">Gridwise Pay Guide</a> ($15/hr floor, ~$17/hr avg).</li>
      </ul>

      <h3>Quartile Methodology</h3>
      <p>Facilities are ranked by <strong>blended competitive wage</strong>, computed as an inverse-distance weighted average of employer wages within {{ data.metadata.distance_cutoff_mi|int }} miles:</p>
      <p style="margin:8px 0;font-family:monospace;background:var(--gray-100);padding:8px 12px;border-radius:4px;">Blended = &Sigma;(wage<sub>i</sub> / dist<sub>i</sub>) / &Sigma;(1 / dist<sub>i</sub>)</p>
      <p>Competitors within {{ data.metadata.distance_cutoff_mi|int }} miles are weighted by 1/distance. Competitors beyond {{ data.metadata.distance_cutoff_mi|int }} miles are excluded (N/A). The 197 locations are divided into quartiles: Q1 (top 25%, highest competitive wages) through Q4 (bottom 25%). Q1 locations face the most competitive hiring environment.</p>

      <h3>Distance Estimates &amp; Cutoff</h3>
      <p>Hover any employer wage cell to see estimated distance to nearest store. If beyond <strong>{{ data.metadata.distance_cutoff_mi|int }} miles</strong>, it is marked N/A and excluded from blended score. Distances are estimated from metro classification and store density.</p>

    </div>
  </div>

</div>

<footer>
  <div class="container">
    Copart Compensation Analysis &middot; Generated {{ data.metadata.generated }} &middot;
    Data: <a href="{{ data.employer_sources.walmart.corporate }}" target="_blank">Walmart</a>,
    <a href="{{ data.employer_sources.home_depot.glassdoor }}" target="_blank">Home Depot</a>,
    <a href="{{ data.employer_sources.costco.corporate }}" target="_blank">Costco</a>,
    <a href="{{ data.employer_sources.starbucks.corporate }}" target="_blank">Starbucks</a>,
    <a href="{{ data.employer_sources.bea_rpp }}" target="_blank">BEA RPP</a>
  </div>
</footer>

<script>
var DATA = {{ data_json }};
var ROLE = { current: 'outdoor' };
var sortState = { col: 'blended', asc: false };
var CUTOFF = DATA.metadata.distance_cutoff_mi || 25;

function assignQuartiles() {
  var key = 'blended_wage_' + ROLE.current;
  var sorted = DATA.locations.slice().sort(function(a, b) { return b[key] - a[key]; });
  var n = sorted.length;
  sorted.forEach(function(loc, i) {
    if (i < n / 4) loc.quartile = 1;
    else if (i < n / 2) loc.quartile = 2;
    else if (i < 3 * n / 4) loc.quartile = 3;
    else loc.quartile = 4;
  });
}

function isInRange(loc, empKey) {
  return loc.in_range && loc.in_range[empKey];
}

function getVal(loc, field, role) {
  role = role || ROLE.current;
  var wm = loc.employers && loc.employers['walmart_' + role];
  var hd = loc.employers && loc.employers['home_depot_' + role];
  var co = loc.employers && loc.employers['costco_' + role];
  var sb = loc.employers && loc.employers['starbucks_' + role];
  switch(field) {
    case 'quartile': return loc.quartile;
    case 'yard': return loc.yard;
    case 'city': return loc.city + ', ' + loc.state;
    case 'walmart': return (wm && isInRange(loc, 'walmart')) ? wm.hourly_avg : null;
    case 'homedepot': return (hd && isInRange(loc, 'home_depot')) ? hd.hourly_avg : null;
    case 'costco': return (co && isInRange(loc, 'costco')) ? co.hourly_avg : null;
    case 'starbucks': return (sb && isInRange(loc, 'starbucks')) ? sb.hourly_avg : null;
    case 'blended': return loc['blended_wage_' + role];
  }
}

function fmtWageWithDist(val, url, title, distMi) {
  if (val == null) return '';
  return '<a class="wage-link" href="' + url + '" target="_blank" title="' + (title||'') + '">$' + val.toFixed(2) + '</a>' +
    '<span class="dist-tip">Nearest: ' + distMi.toFixed(1) + ' mi</span>';
}

function blendedCell(loc, role) {
  var val = loc['blended_wage_' + role];
  var dist = loc.nearest_distance_mi || {};
  var emps = loc.employers || {};
  var keys = [
    {name: 'WMT', short: 'walmart', full: 'walmart_' + role},
    {name: 'HD', short: 'home_depot', full: 'home_depot_' + role},
    {name: 'COST', short: 'costco', full: 'costco_' + role},
    {name: 'SBUX', short: 'starbucks', full: 'starbucks_' + role}
  ];
  var parts = [];
  var totalW = 0;
  keys.forEach(function(k) {
    if (isInRange(loc, k.short) && emps[k.full]) {
      var w = 1.0 / dist[k.short];
      parts.push({name: k.name, wage: emps[k.full].hourly_avg, weight: w});
      totalW += w;
    }
  });
  var tip = '';
  if (totalW > 0) {
    tip = parts.map(function(p) {
      return Math.round(p.weight / totalW * 100) + '% ' + p.name;
    }).join(' + ');
  }
  return '<td class="wage-cell"><strong>$' + val.toFixed(2) + '</strong>' +
    (tip ? '<span class="dist-tip">' + tip + '</span>' : '') + '</td>';
}

function empCell(emp, empKey, loc, role) {
  var e = loc.employers && loc.employers[empKey + '_' + role];
  var dist = loc.nearest_distance_mi || {};
  var shortKey = empKey === 'home_depot' ? 'home_depot' : emp.toLowerCase();
  if (e && isInRange(loc, shortKey)) {
    return '<td class="wage-cell">' + fmtWageWithDist(e.hourly_avg, e.source_url, e.source_name, dist[shortKey] || 0) + '</td>';
  }
  return '<td class="na-cell" title="Nearest ' + emp + ': ' + (dist[shortKey] || 0).toFixed(1) + ' mi (>' + CUTOFF + ' mi cutoff)">N/A</td>';
}

function computeStats(locs, field, role) {
  var vals = [];
  locs.forEach(function(l) {
    var v = getVal(l, field, role);
    if (v != null) vals.push(v);
  });
  if (vals.length === 0) return null;
  vals.sort(function(a,b) { return a-b; });
  var sum = vals.reduce(function(a,b) { return a+b; }, 0);
  var mean = sum / vals.length;
  var median = vals.length % 2 === 0
    ? (vals[vals.length/2-1] + vals[vals.length/2]) / 2
    : vals[Math.floor(vals.length/2)];
  return { mean: mean, median: median, count: vals.length };
}

function statCell(locs, field, role) {
  var s = computeStats(locs, field, role);
  return s ? '$' + s.mean.toFixed(2) : '&mdash;';
}
function statCellMed(locs, field, role) {
  var s = computeStats(locs, field, role);
  return s ? '$' + s.median.toFixed(2) : '&mdash;';
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
  var cols = 8;

  locs.forEach(function(loc, idx) {
    if (!qGroups[loc.quartile]) qGroups[loc.quartile] = [];
    qGroups[loc.quartile].push(loc);

    var prevLoc = idx > 0 ? locs[idx - 1] : null;
    var isFirst = !prevLoc || prevLoc.quartile !== loc.quartile;

    html += '<tr' + (isFirst ? ' class="q-first"' : '') + '>';
    html += '<td><span class="q-badge q' + loc.quartile + '">Q' + loc.quartile + '</span></td>';
    html += '<td><strong>' + loc.yard + '</strong><div class="yard-addr">' + loc.address + ', ' + loc.city + ', ' + loc.state + ' ' + loc.zip + '</div></td>';
    html += '<td>' + loc.city + ', ' + loc.state + '</td>';
    html += empCell('Walmart', 'walmart', loc, role);
    html += empCell('Home Depot', 'home_depot', loc, role);
    html += empCell('Costco', 'costco', loc, role);
    html += empCell('Starbucks', 'starbucks', loc, role);
    html += blendedCell(loc, role);
    html += '</tr>';

    var nextLoc = locs[idx + 1];
    if (!nextLoc || nextLoc.quartile !== loc.quartile) {
      var group = qGroups[loc.quartile];
      // Mean row
      html += '<tr class="subtotal-row mean-row">';
      html += '<td><span class="q-badge q' + loc.quartile + '">Q' + loc.quartile + '</span></td>';
      html += '<td colspan="2"><strong>Mean</strong> (' + group.length + ' locations)</td>';
      html += '<td>' + statCell(group, 'walmart', role) + '</td>';
      html += '<td>' + statCell(group, 'homedepot', role) + '</td>';
      html += '<td>' + statCell(group, 'costco', role) + '</td>';
      html += '<td>' + statCell(group, 'starbucks', role) + '</td>';
      html += '<td><strong>' + statCell(group, 'blended', role) + '</strong></td>';
      html += '</tr>';
      // Median row
      html += '<tr class="subtotal-row median-row">';
      html += '<td></td>';
      html += '<td colspan="2"><strong>Median</strong></td>';
      html += '<td>' + statCellMed(group, 'walmart', role) + '</td>';
      html += '<td>' + statCellMed(group, 'homedepot', role) + '</td>';
      html += '<td>' + statCellMed(group, 'costco', role) + '</td>';
      html += '<td>' + statCellMed(group, 'starbucks', role) + '</td>';
      html += '<td><strong>' + statCellMed(group, 'blended', role) + '</strong></td>';
      html += '</tr>';
      // Spacer between quartiles
      if (nextLoc) {
        html += '<tr class="q-spacer"><td colspan="' + cols + '"></td></tr>';
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
  var isIndoor = document.getElementById('roleToggle').checked;
  ROLE.current = isIndoor ? 'indoor' : 'outdoor';
  document.getElementById('lbl-outdoor').classList.toggle('active', !isIndoor);
  document.getElementById('lbl-indoor').classList.toggle('active', isIndoor);
  assignQuartiles();
  renderTable();
}

function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
  document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelector('.tab-btn[onclick*="' + tab + '"]').classList.add('active');
}

document.addEventListener('DOMContentLoaded', function() {
  assignQuartiles();
  renderTable();
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
