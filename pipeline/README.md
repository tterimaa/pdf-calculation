# Calculation pipeline

Script calculate_all.py calculates all impact factors at once based on the arguments provided in arguments.json file. The purpose of the script is to provide a convenient and reproducible way to perform the calculations. Collecting all important variables of the calculation in arguments.json file makes the calculation transparent and easily adjustable.

## How to run the calculation

1. Download lc impact and exiobase databases and place them somewhere on your filesystem
2. Change lc_impact_path and exio_19_path accordingly
3. Install dependencies: ```pip install -r requirements.txt```
4. ```python pipeline/calculate-all.py pipeline/arguments.json ```

Output files should appear in pipeline/output directory.

## Notes
- Exiobase and lc-impact versions are currently not dynamic, meaning user of the script needs to manually download correct exiobase version. To make this 100% reproducible, these files should be downloaded and verified based on version number.