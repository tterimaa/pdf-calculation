import pymrio
import numpy as np
import pandas as pd
import pycountry as pyc
import json
import argparse


def calculate_all(lci_path):
    # load and prepare lc-impact data

    # for climate change 
    # TODO: check if it's correct to use 'all effects 100yrs'
    lci_climate = pd.read_excel(f"{lci_path}/2-climate change/Climate change CFs.xlsx", 
                                sheet_name=" Characterization factors",
                                header=[0,1])
    lci_climate = lci_climate.iloc[:4, [0, 6, 10]] # select 'substance', 'terrestrial all effects 100yrs', 'aquatic all effects 100yrs'
    lci_climate.columns = [' '.join(col).strip() for col in lci_climate.columns]
    lci_climate.rename(columns={lci_climate.columns[0]: "Substance", lci_climate.columns[1]: "All effects 100yrs (terrestrial)", lci_climate.columns[2]: "All effects 100yrs (aquatic)"}, inplace=True)

    # for photochemical ozone formation
    # this is clear, only one option for factors
    lci_ozone = pd.read_excel(f"{lci_path}/5-photochemical ozone formation/Photochemical_Ozone_formation.xlsx",
                    sheet_name="CFs per country",
                    skiprows=0,
                    header=[0,1])
    lci_ozone.columns = [' '.join(col).strip() for col in lci_ozone.columns]
    lci_ozone.rename(columns={lci_ozone.columns[0]: "Country", lci_ozone.columns[4]: "NOx", lci_ozone.columns[5]: "NMVOC"}, inplace=True)
    lci_ozone.drop(columns=[lci_ozone.columns[1], lci_ozone.columns[2], lci_ozone.columns[3]], inplace=True)

    # for terrestrial acidification
    # this is clear, only one option for factors
    lci_acidification = pd.read_excel(f"{lci_path}/7-terrestrial acidification/CF_terrestrial_acidification.xlsx",
                    sheet_name="CF per countries",
                    skiprows=0,
                    header=[0,1],
                    na_values=[' '])
    lci_acidification.dropna(inplace=True) # for some reason there are empty rows in acidification data
    lci_acidification.columns = [' '.join(col).strip() for col in lci_acidification.columns]
    lci_acidification.rename(columns={lci_acidification.columns[0]: "Country", lci_acidification.columns[1]: "CF Nox", lci_acidification.columns[2]: "CF NH3",lci_acidification.columns[3]: "CF Sox"}, inplace=True)

    # for freshwater eutrophication
    # TODO: check if this average approach is correct
    lci_freshwater_eutrophication = pd.read_excel(f"{lci_path}/8-freshwater eutrophication/CF_FWEutrophication.xlsx",
                    sheet_name="Country CFs")
    # take average of phosphorus emissions to water and soil
    lci_freshwater_eutrophication["Average"] = lci_freshwater_eutrophication[["CF for P emissions to water [PDFyr/kg]", "CF for P emissions to soil [PDFyr/kg]"]].mean(axis=1)
    lci_freshwater_eutrophication = lci_freshwater_eutrophication[["Country", "Average"]]

    # for marine eutrophication
    # TODO: check if selected columns below are correct, only direct N emissions to marine system are used?
    lci_marine_eutrophication = pd.read_excel(f"{lci_path}/9-marine eutrophication/CFs_marine_eutrophication.xlsx",
                    sheet_name="country CFs")
    lci_marine_eutrophication = lci_marine_eutrophication[["Country.1", "CF for direct N emission to marine system [PDF*yr/kg]"]]
    lci_marine_eutrophication.rename(columns={lci_marine_eutrophication.columns[0]: "Country"}, inplace=True)

    # for land use 
    # TODO: should we use average or marginal factors?
    # TODO: should transformation be taken into account, now only occupation is used?
    lci_land = pd.read_excel(f"{lci_path}/11-Land stress/CFs_land_Use_average.xlsx",
                    sheet_name="occupation average country",
                    skiprows=1,
                    header=[0,1])
    lci_land.columns = [' '.join(col).strip() for col in lci_land.columns]
    lci_land.rename(columns={lci_land.columns[0]: "Country"}, inplace=True)
    lci_land = lci_land[["Country", "Annual crops Median", "Permanent crops Median", "Pasture Median", "Extensive forestry Median", "Intensive forestry Median", "Urban Median"]]
    # Calculate the mean of forest land use types 
    lci_land["Forestry Median"] = lci_land[["Extensive forestry Median", "Intensive forestry Median"]].mean(axis=1)
    lci_land = lci_land[["Country", "Annual crops Median", "Permanent crops Median", "Pasture Median", "Forestry Median", "Urban Median"]]

    # for water use
    # TODO: should we use 'all effects' or 'certain effects'?
    lci_water = pd.read_excel(f"{lci_path}/12-water consumption/CFs_water_consumption_ecosystems_20180831.xlsx",
                        sheet_name="CF per countries",
                        dtype={1: float, 2: float},
                        skiprows=2)
    lci_water = lci_water[["Country", "CF all effects  [PDF·yr/m3]"]]
    print(lci_water)


def main():
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("json_file", type=str, help="Path to the JSON file.")
    
    # Parse the arguments
    args = parser.parse_args()
    json_file = args.json_file

    try:
        # Open and read the JSON file
        with open(json_file, 'r') as file:
            data = json.load(file)
        
        # Print the parsed JSON data
        print("Successfully parsed JSON file:")
        print(json.dumps(data, indent=4))  # Pretty-print JSON

        calculate_all(data['lc_impact_path'])
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON file. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()