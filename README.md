# Campus Complaint Portal Dashboard

**Course:** CSDC0207 Data Visualization for Product Design

An interactive dashboard that analyses complaints from a college complaint portal
(Hostel, Classroom & Lab, Other). Built with Python, Streamlit, Plotly and pandas.

## Problem statement
Administration and hostel wardens need to know what is broken, where, and how fast it is fixed.

## Questions the dashboard answers
1. Which problems are most frequent?
2. Which block or building has the most issues?
3. Which categories take the longest to resolve?
4. Is the situation improving over time?

## Features
- KPI cards: total complaints, open, % resolved, most frequent issue
- Charts: area, donut, bar, location heat map, word cloud, scatter with regression line (each can be enlarged in a pop-up)
- Hotspot table and CSV download
- Filters: section, status, date range
- Data cleaning log (duplicates, inconsistent names, missing resolve dates)
- Option to upload your own CSV

## Syllabus mapping
| Unit | Used in project |
|------|-----------------|
| 1 | Data types (nominal, ordinal, numeric, time series) |
| 2 | Cleaning: duplicates, consistency check, missing data |
| 3 | Mean, median, std dev, quartiles, percentiles |
| 4 | Regression line (volume vs. resolution time) |
| 5 | Tufte data-ink, Gestalt grouping, ethics, storytelling, dashboard design |

## Data
Synthetic dataset (about 600 complaints) generated in `app.py` to mirror the portal structure.
To use real data, upload a CSV with columns:
`complaint_id, submitted, category, section, location, keyword, status, resolved`

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Ethics
Data is anonymised. No student names or room numbers are shown; location is at block or building level.

## Author
YOUR NAME, ROLL NO, BRANCH
