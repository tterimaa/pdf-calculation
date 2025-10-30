# Calculate PDF/€ impact factors by combining data from exiobase and lc-impact

The code in this repository demonstrates how to calculate consumption based impact factors PDF/€ by combining data from exiobase and lc-impact. PDF (potentially disappeared fraction of species) is a metric used in biodiversity impact assesments to quantify the potential impact of human activities on biodiversity. The methodology aims to follow the one presented in "Value-transforming financial, carbon and biodiversity footprint accounting" by S. El Geneidy, S. Baumeister, M. Peura, and J.S. Kotiaho.

## Repository structure

pipeline directory contains a script calculate-all.py that automates the full calculation process.

notebooks directory contains jupyter notebooks to demonstrate the calculation process step-by-step. The notebooks can also be used to check intermediate results and debug calculation steps.

The root directory contains arguments.json file which is used as a parameter for both the automated pipeline and the notebooks. This file contains most of the essential parameters for the calculation.

## Methodology Overview

This methodology combines EXIOBASE (economic and environmental data) with LC-IMPACT (biodiversity characterization factors) to calculate consumption-based biodiversity impact factors (PDF/€).

### Simplified Example: Land Use from Agriculture

Let's trace how consuming €1 of agricultural products in Finland impacts biodiversity globally. This example uses 2 consumption countries × 2 sectors, but the real calculation uses 49 regions × 200 sectors.

```
DATA SOURCES:
┌──────────────────────────────────────────────────────────────┐
│ EXIOBASE: Supply chains + Environmental stressors            │
│ • Where products come from                                   │
│ • How much land is used by each region-sector (m²)           │
└──────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────┐
│ LC-IMPACT: Biodiversity characterization factors             │
│ • How sensitive is biodiversity in each country (PDF/m²)     │
└──────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
STEP 1: Driver Origin (DRorigin) - Where does land use occur?
═══════════════════════════════════════════════════════════════

EXIOBASE traces supply chains: When Finland consumes €1 of agriculture,
land is used in Finland, Brazil (imports), and other countries.

                    Consumption in →
                    FI-Agr    FI-Mfg    BR-Agr    BR-Mfg
Impact occurs in ↓  (€1)      (€1)      (€1)      (€1)
─────────────────────────────────────────────────────────
FI-Agriculture     800 m²    100 m²     20 m²     50 m²
FI-Manufacturing    50 m²    600 m²     10 m²    200 m²
BR-Agriculture     150 m²     50 m²    900 m²    100 m²
BR-Manufacturing    20 m²    300 m²     80 m²    700 m²
─────────────────────────────────────────────────────────
                  1020 m²   1050 m²   1010 m²   1050 m²  (column sums)

Example: €1 of Finnish agriculture uses 800 m² in Finland + 150 m²
in Brazil (imported inputs) + 50+20 m² in manufacturing sectors.

═══════════════════════════════════════════════════════════════
STEP 2: Driver Share (DRshare) - Normalize to shares
═══════════════════════════════════════════════════════════════

Divide each column by its sum to get shares (each column sums to 1.0):

                    Consumption in →
                    FI-Agr    FI-Mfg    BR-Agr    BR-Mfg
Impact occurs in ↓
─────────────────────────────────────────────────────────
FI-Agriculture      0.78      0.10      0.02      0.05
FI-Manufacturing    0.05      0.57      0.01      0.19
BR-Agriculture      0.15      0.05      0.89      0.10
BR-Manufacturing    0.02      0.29      0.08      0.67
─────────────────────────────────────────────────────────
                    1.00      1.00      1.00      1.00

Example: When Finland consumes €1 of agriculture, 78% of land
impacts occur in Finland, 15% in Brazil, etc.

═══════════════════════════════════════════════════════════════
STEP 3: Region Harmonization (DRunit) - Expand ROW regions
═══════════════════════════════════════════════════════════════

EXIOBASE has "Rest of World" aggregated regions (WA, WE, WF, WL, WM).
These are expanded to individual countries for LC-IMPACT matching.

Example: "WL" (Rest of Latin America) gets split into Argentina,
Chile, Colombia, etc. Each country gets an equal share.

Before: WL-Agriculture = 0.20
After:  AR-Agriculture = 0.20/30 = 0.0067
        CL-Agriculture = 0.20/30 = 0.0067
        CO-Agriculture = 0.20/30 = 0.0067
        ... (30 countries)

This expands the matrix from ~9,800 rows to ~48,000 rows.

═══════════════════════════════════════════════════════════════
STEP 4: Monetary Factors (DRfactor) - Convert to stressor/€
═══════════════════════════════════════════════════════════════

Apply EXIOBASE stressor intensity (m²/€) to get actual land use per €:

Stressor intensity:    FI-Agr: 1020 m²/€
                       FI-Mfg: 1050 m²/€
                       BR-Agr: 1010 m²/€
                       BR-Mfg: 1050 m²/€

Multiply each column by its intensity:

                    Consumption in →
                    FI-Agr    FI-Mfg    BR-Agr    BR-Mfg
Impact occurs in ↓  (m²/€)    (m²/€)    (m²/€)    (m²/€)
─────────────────────────────────────────────────────────
FI-Agriculture      796       105        20        53
FI-Manufacturing     51       598        10       200
BR-Agriculture      153        53       899       105
BR-Manufacturing     20       304        81       704
─────────────────────────────────────────────────────────

Example: €1 of FI-Agriculture → 796 m² in Finland, 153 m² in Brazil

═══════════════════════════════════════════════════════════════
STEP 5: Biodiversity Impact (PDF/€) - Apply LC-IMPACT factors
═══════════════════════════════════════════════════════════════

LC-IMPACT provides characterization factors (PDF/m²) for each country:

                    CF (PDF/m²)
─────────────────────────────────
FI-Agriculture      5.0 × 10⁻¹⁶
FI-Manufacturing    3.0 × 10⁻¹⁶
BR-Agriculture      8.0 × 10⁻¹⁶
BR-Manufacturing    4.0 × 10⁻¹⁶

Multiply m²/€ by PDF/m² and sum over impact countries:

FI-Agriculture consumption:
  = (796 m² × 5.0×10⁻¹⁶) + (51 × 3.0×10⁻¹⁶) + (153 × 8.0×10⁻¹⁶) + (20 × 4.0×10⁻¹⁶)
  = 3.98×10⁻¹³ + 1.53×10⁻¹⁴ + 1.22×10⁻¹³ + 8.0×10⁻¹⁵
  = 5.48 × 10⁻¹³ PDF/€

FINAL OUTPUT (example):
─────────────────────────────────
FI-Agriculture:  5.48 × 10⁻¹³ PDF/€
FI-Manufacturing: 4.21 × 10⁻¹³ PDF/€
BR-Agriculture:  6.92 × 10⁻¹³ PDF/€
BR-Manufacturing: 5.15 × 10⁻¹³ PDF/€

This means: Consuming €1 of Finnish agricultural products causes
5.48 × 10⁻¹³ PDF of biodiversity impact globally (mostly in Brazil
where CF is higher).
```

### Key Concepts

**Consumption-based accounting**: Impacts are attributed to final consumption, not where they physically occur. The Leontief input-output model traces impacts through multi-tier supply chains.

**Real dimensions**:
- 49 EXIOBASE regions × 200 sectors = 9,800 consumption region-sector pairs
- 240 LC-IMPACT countries × 200 sectors = 48,000 impact country-sector pairs

**PDF (Potentially Disappeared Fraction)**: Fraction of species potentially lost, integrated over area and time. Units are PDF×m²×year or PDF×year per euro of consumption.

## Calculation details

Calculation is performed as granularly as possible, meaning if CF from lc-impact can be connected to exiobase categories it's calculated separately even though it would be part of a group such as 'land use'. Exiobase categories and lc-impact stressors used in calculations can be found in the beginning of every notebook. Impact factors can be divided into following categories:

1. Land stress (pdf-land.ipynb)
- Forestry
- Annual crops
- Annual / permanent crops
- Pasture
- Other land use
2. Climate (pdf-climate.ipynb)
- Climate change (terrestrial ecosystems)
- Climate change (aquatic ecosystems)
3. Direct exploitation of natural resources (pdf-water.ipynb)
- Water stress
4. Pollution (pdf-eutrophication-freshwater.ipynb, pdf-eutrophication-marine.ipynb, pdf-pollution-acid.ipynb, pdf-pollution-ozone.ipynb)
- Freshwater eutrophication from P emissions to water
- Freshwater eutrophication from P emissions to soil
- Marine eutrophication from N emissions to marine systems
- Terrestrial acidification (NOx)
- Terrestrial acidification (SOx)
- Terrestrial acidification (NH3)
- Photochemical ozone formation (NMVOC)
- Photochemical ozone formation (NOx)

The impact factors for top-level categories can be calculated by summing up its components.

## Notes about regional harmonization
- Data in lc-impact is not consistent with regions. Some regions that can be found from exiobase are not found in lc-impact, but these missing regions are not consistent across the whole database. For example, water stress impact factors are missing for Malta, and land use factors are missing Taiwan. For missing factors, continental averages were used.
- Mapping the rest of the world regions in exiobase to lc-impact regions that are not present as direct regions in exiobase is one of the key parameters of these calculations. These mappings are not carefully thought out and should be re-evaluated. For example, some sub-regions of countires might have been left out.

## Q&A

In general, most of the inclarity regarding the methodology is related to what are the 'connecting stressor in LC-impact' (table S5) exactly. LC-impact provides more than one option for the CFs.

### Freshwater eutrophication

Q: It's clear that "P - agriculture - water" connects to "CF for P emissions to water" and "P - agriculture - soil" connects to "CF for P emissions to soil" but there's also CF for erosion. Is it correct that this is not used because of lack of connecting information in exiobase? 
A:

### Marine eutrophication

Q: Only obvious connection I could find from lc-impact was 'CF for direct N emission to marine system' is used. Is this enough for calulating marine eutrophication?
A:

### Water stress

Q: Should we use 'all effects' or 'certain effects'?
A: 

### Land stress

Q: Should land use take into account both occupation and transformation? Right now the factors are calculated with only occupation CFs. If transformation should be taken into account, should it use median values from transf. avg country 100y (CFs_land_Use_average.xlsx)?
A: 

Q: Is the connecting stressor in LC-impact for other land use correct? According to the paper it's 'Average of remaining land use types in LC-Impact (Urban)' but in LC-impact land stress data there is only one remaining land use type which is urban. What is the average paper is referring to?
A:

### Climate

Q: What is the correct exiobase stressor for climate? Table S5 mentions 'Climate change midpoint | ILCD recommended CF | Global warming potential 100 years' but on the other hand it's mentioned that 'In terms of the biodiversity impacts of climate change, we take into account carbon dioxide, methane, fossil methane and nitrous oxide'. How do you connect these two?

The calculation code (see pipeline/calculate_all.py row 754) makes an attempt to group the above mentioned substances into the four groups, multiplying those amounts by the respective PDF*y/kg factors and then summing up the factors for different substances to get the total factors for both aquatic and terrestrial effects. If grouping pattern should be used, is it correct? Check exiobase_grouping_patterns.climate_change in arguments.json.

This sentence in the paper hints that grouping to different substances should be done: 'With the spatial component missing from the climate change biodiversity impact analyses, we then multiplied the biodiversity impact factor of each gas with its respective counterpart factor in EXIOBASE'. However, it's unclear how the grouping should be done exactly and why Table S5 does not mention this.
A:

Q: Is it correct to use 'all effects 100yrs'
A: (please confirm) Yes. Citation from the paper: 'We chose impact factors that take all effects into
account for a period of 100 years for both terrestrial and aquatic ecosystems'.

### General

Q: Are all grouping patterns in arguments.json ok?
A: 

Q: Are rest of the world countries correctly grouped to different regions in arguments.json?
A:

## Proposals for maximal reproducibility
1. Add more details of connecting lc-impact stressors (Table S5). For example, for 'Land stress: Annual crops' specify file name (CFs_land_Use_average.xlsx), sheet (occupation average country) and column name (Aggregated [PDF-eq/m2] - Core and extended value (no difference) / Annual crops / Median)
2. If multiple exiobase categories needs to be aggregated, add used regular expressions similar to what was found for water in the code snippet in supporting information: 'Water Consumption Blue.*'
3. Best option that would remove the need for adding details to the text would be to publish code that can be used to reproduce the results. End-to-end pipeline similar to pipeline/calculate-all.py would contain all necessary details of the calculation.