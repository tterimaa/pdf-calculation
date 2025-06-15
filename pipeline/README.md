# Calculation pipeline

Script calculate_all.py calculates all impact factors at once based on the arguments provided in arguments.json file. The purpose of the script is to provide a convenient and reproducible way to perform the calculations. Collecting all important variables of the calculation in arguments.json file makes the calculation transparent and easily adjustable.

## How to run the calculation

1. Download lc impact and exiobase databases and place them somewhere on your filesystem
2. Change lc_impact_path and exio_19_path accordingly
3. Install dependencies: ```pip install -r requirements.txt```
4. ```python pipeline/calculate-all.py pipeline/arguments.json ```

Output files should appear in pipeline/output directory.

### Optional command line arguments

- `--store-matrix`: Store dr_f matrices as pickle files to the output/matrices directory. These matrices contain the regional distribution of environmental impacts per euro spent.

  Example: ```python pipeline/calculate-all.py pipeline/arguments.json --store-matrix```
  
  The matrices will be saved with names like `pdf-matrix-ozone-nmvoc.pkl`, `pdf-matrix-land-forestry.pkl`, etc., and can be loaded in Python using the pickle module. Note that climate impact matrices are not stored as they are not regionally distributed.

## Notes
- Exiobase and lc-impact versions are currently not dynamic, meaning user of the script needs to manually download correct exiobase version. To make this 100% reproducible, these files should be downloaded and verified based on version number.