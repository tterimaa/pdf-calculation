# Calculate PDF/€ impact factors by combining data from exiobase and lc-impact

The code in this repository demonstrates how to calculate consumption based impact factors PDF/€ by combining data from exiobase and lc-impact. PDF (potentially disappeared fraction of species) is a metric used in biodiversity impact assesments to quantify the potential impact of human activities on biodiversity. The methodology aims to follow the one presented in "Value-transforming financial, carbon and biodiversity footprint accounting" by S. El Geneidy, S. Baumeister, M. Peura, and J.S. Kotiaho.

## Repository structure

pipeline directory contains a script calculate-all.py that automates the full calculation process.

notebooks directory contains jupyter notebooks to demonstrate the calculation process step-by-step. The notebooks can also be used to check intermediate results and debug calculation steps.

The root directory contains arguments.json file which is used as a parameter for both the automated pipeline and the notebooks. This file contains most of the essential parameters for the calculation.

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