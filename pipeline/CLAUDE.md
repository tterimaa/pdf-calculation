# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based calculation pipeline for environmental impact factors. The project calculates Probability of Disappearance of Fractions (PDF) per euro for various environmental impact categories including climate change, ozone formation, acidification, eutrophication, land use, and water consumption.

## Core Architecture

- **Main calculation script**: `calculate-all.py` - orchestrates all calculations based on configuration in `arguments.json`
- **Configuration**: `arguments.json` - contains all important variables including database paths and region mappings
- **Country harmonization**: `countries.py` - provides an example how countries between exiobase and lc-impact should be harmonized 
- **Output directory**: `output/` - contains generated CSV files with calculated impact factors

The pipeline combines:
- LC-Impact characterization factors (environmental impact per unit of stressor)
- EXIOBASE input-output tables (economic data for 2011 and 2019)
- Custom region mapping for "rest of world" countries not explicitly in EXIOBASE

## Key Data Flow

1. Load LCI (Life Cycle Impact) characterization factors from Excel files
2. Load EXIOBASE economic data (uses 2011 for consumption patterns, 2019 for impact factors)
3. Calculate consumption-based accounts (CBA) to determine regional stressor distributions
4. Apply characterization factors to calculate environmental impact per euro spent
5. Output results as CSV files for each impact category

## Core concepts explained
- **ROW regions**: row regions mean 'rest of the world regions'. These are countries or
regions that don't exist in EXIOBASE data but they exist in lc-impact. EXIOBASE data
contains five 'rest of the world' region categories: asia pacific, americas, africa, middle east
and europe. Harmonizing regions means taking the countries from a specific lc-impact
dataset, checking which ones are not directly found from EXIOBASE and categorizing
these not found countries into rest of the world regions.
- **cba**: cba refers to 'consumption-based accounts' which means how impacts of consumption
are distributed across impact regions. D_cba is a matrix where each column is a country-product
pair (consumption region) and rows tell the impacts in different impact regions.
- **dr_s**: dr_s is a normalized version of cba. It tells the share of the impact in different
impact regions. It tells the percentage of impacts occurring in different impact regions (rows)
that are driven by consumption in consumption region.
- **dr_u**: dr_u is augmented version of dr_s. In the augmentation process, the countries that
don't exist in EXIOBASE are added to dr_s. The value for each new region is the value of the
corresponding region (e.g. asia) divided by the number of countries in that region. Thus the
calculation assumes that the impacts are evenly distributed across the region.
- **dr_f** is formed by multiplying the consumption-based impact factor (impact/€ spent)
by respective columns of dr_u. This results in a new matrix which tells how the impact of
1€ spent is distributed to impact regions.

## Common Commands

Run the full calculation pipeline:
```bash
python pipeline/calculate-all.py pipeline/arguments.json
```

Test country/region harmonization:
```bash
python pipeline/countries.py
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Key Configuration

All paths and parameters are configured in `arguments.json`:
- `lc_impact_path`: Path to LC-Impact characterization factors
- `exio_19_path`: Path to EXIOBASE 2019 data 
- `exio_11_path`: Path to EXIOBASE 2011 data
- `row_region_mappings`: Mappings for rest-of-world countries to continental regions

## Dependencies

The project uses several specialized libraries:
- `pymrio`: EXIOBASE input-output analysis
- `pandas`: Data manipulation
- `numpy`: Numerical calculations  
- `pycountry`: Country code standardization

## Important Notes

- EXIOBASE and LC-Impact databases must be downloaded separately and paths configured
- The calculation uses 2011 consumption patterns but 2019 impact factors
- Region mappings handle countries not explicitly included in EXIOBASE by grouping them into continental "rest of world" regions
- All TODO comments in the code indicate methodological decisions that may need review
