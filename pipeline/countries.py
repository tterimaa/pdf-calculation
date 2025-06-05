import pandas as pd
import pymrio
import pycountry as pyc
import json

"""
This file is for testing harmonization of LCI and exiobase data regarding countries and regions.
"""

def load_lci(lci_path):
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
    return lci_climate, lci_ozone, lci_acidification, lci_freshwater_eutrophication, lci_marine_eutrophication, lci_land, lci_water

def get_country_code(name):
    # custom mappings for countries that pycountry does not recognize
    # these should cover all the countries in the LCI data if country has alpha-2 code
    # these mappings were extracted manually
    extra_mappings = {
        "Turkey": "TR",
        "Russia": "RU",
        "Bahamas, The": "BS",
        "Bonaire": "BQ",
        "Byelarus": "BY",
        "Brunei": "BN",
        "Cape Verde": "CV",
        "Cocos Islands": "CC",
        "Congo DRC": "CD",
        "China, Hong Kong Special Administrative Region": "HK",
        "Curacao": "CW",
        "Democratic Republic of the Congo": "CD",
        "Falkland Islands": "FK",
        "Falkland Islands (Islas Malvinas)": "FK",
        "Gambia, The": "GM",
        "Gaza Strip": "PS",
        "Heard Island & McDonald Islands": "HM",
        "Ivory Coast": "CI",
        "Macedonia": "MK",
        "The Former Yugoslav Republic of Macedonia": "MK",
        "Macau": "MO",
        "Man, Isle of": "IM",
        "Micronesia": "FM",
        "Myanmar (Burma)": "MM",
        "Netherlands Antilles": "AN",
        "Palestinian Territory": "PS",
        "Pacific Islands (Palau)": "PW",
        "Pitcairn Islands": "PN",
        "Reunion": "RE",
        "Saba": "BQ",
        "Saint Eustatius": "BQ",
        "Saint Helena": "SH",
        "Saint Martin": "MF",
        "Sint Maarten": "SX",
        "South Georgia and the South Sandwich Is": "GS",
        "South Georgia": "GS",
        "St. Helena": "SH",
        "Saint Barthelemy": "BL",
        "Saint Kitts and Nevis": "KN",
        "St. Kitts and Nevis": "KN",
        "St. Lucia": "LC",
        "St. Pierre and Miquelon": "PM",
        "Sao Tomo and Principe": "ST",
        "St. Vincent and the Grenadines": "VC",
        "Svalbard": "SJ",
        "Jan Mayen": "SJ",
        "Swaziland": "SZ",
        "US Virgin Islands": "VI",
        "Virgin Islands": "VG",
        "Western Samoa": "WS",
        "West Bank": "PS",
    }
    try:
        return pyc.countries.lookup(name).alpha_2
    except LookupError:
        try:
            return extra_mappings[name]
        except LookupError:
            print("Alpha-2 country code does not exist for ", name)
            return None

def get_row_regions(lci_country_codes, exio_country_codes):
    """
    Get the country codes from lci countries that don't exist in exiobase i.e. rest of the world countries.
    """
    row_regions = []
    for country in lci_country_codes:
        if country not in exio_country_codes:
            row_regions.append(country)

    # find duplicates in the list
    duplicates = []
    unique_regions = []
    seen_once = set()
    for item in row_regions:
        if item not in seen_once:
            unique_regions.append(item)
            seen_once.add(item)
        else:
            duplicates.append(item)
    print("Duplicates found in row regions:", duplicates)
    return unique_regions

def augment_water(lci_water):
    # malta is missing from lc-impact, add malta as new row with country code MT and EU averages
    cf_certain_eu = 4.57E-15
    cf_all_eu = 9.02E-15
    row = pd.DataFrame({
        "Country": ["Malta"],
        "CF certain effects [PDF·yr/m3]": [cf_certain_eu],
        "CF all effects  [PDF·yr/m3]": [cf_all_eu],
        "Country_Code": ["MT"],
    })
    lci_water = pd.concat([lci_water, row], ignore_index=True)
    return lci_water

def augment_land(lci_land):
    # taiwan is missing from lc-impact, add taiwan as new row with country code TW and asia averages
    cf_annual_asia = 1.4159650959661E-15
    cf_permanent_asia = 1.02741974515257E-15
    cf_average_asia = (cf_annual_asia + cf_permanent_asia) / 2
    row = pd.DataFrame({
        "Country": ["Taiwan"],
        "Average": [cf_average_asia],
        "Annual crops Median": [cf_annual_asia],
        "Permanent crops Median": [cf_permanent_asia],
        "Pasture Median": [cf_annual_asia],
        "Country_Code": ["TW"],
    })
    lci_land = pd.concat([lci_land, row], ignore_index=True)
    return lci_land

def augment_freshwater(lci_freshwater):
    # malta is missing from lc-impact, add malta as new row with country code MT and EU averages
    p_w_eu = 2.19740701963604E-13
    p_s_eu = 2.27816881528299E-14
    p_avg_eu = (p_w_eu + p_s_eu) / 2
    malta_row = pd.DataFrame({
        "Country": ["Malta"],
        "CF for P emissions to water [PDFyr/kg]": [p_w_eu],
        "CF for P emissions to soil [PDFyr/kg]": [p_s_eu],
        "Average": [p_avg_eu],
        "Country_Code": ["MT"],
    })
    lci_freshwater = pd.concat([lci_freshwater, malta_row], ignore_index=True)
    # cyprus is missing from lc-impact, add cyprus as new row with country code CY and EU averages
    cyprus_row = pd.DataFrame({
        "Country": ["Cyprus"],
        "CF for P emissions to water [PDFyr/kg]": [p_w_eu],
        "CF for P emissions to soil [PDFyr/kg]": [p_s_eu],
        "Average": [p_avg_eu],
        "Country_Code": ["CY"],
    })
    lci_freshwater = pd.concat([lci_freshwater, cyprus_row], ignore_index=True)
    return lci_freshwater

def augment_marine(lci_marine):
    n_w_eu = 3.86913531769129E-15
    luxembourg_row = pd.DataFrame({
        "Country": ["Luxembourg"],
        "Country_Code": ["LU"],
        "CF for direct N emission to marine system [PDF*yr/kg]": [n_w_eu],
    })
    switzerland_row = pd.DataFrame({
        "Country": ["Switzerland"],
        "Country_Code": ["CH"],
        "CF for direct N emission to marine system [PDF*yr/kg]": [n_w_eu],
    })
    lci_marine = pd.concat([lci_marine, luxembourg_row, switzerland_row], ignore_index=True)
    return lci_marine

def get_missing_from_lci(exio_regions, lci):
    """
    Get the regions that are in exiobase but not in lci data.
    """
    missing = []
    for region in exio_regions:
        if region not in lci["Country_Code"].tolist():
            missing.append(region)
    return missing

def augment_acid(lci_acidification):
    # taiwan and malta are missing from lc-impact
    cf_nox_asia = 2.68501157634878E-14
    cf_nh3_asia = 5.72697601775371E-15
    cf_sox_asia = 2.13657207308791E-14

    cf_nox_europe = 3.88566620512411E-14
    cf_nh3_europe = 1.209421972687E-14
    cf_sox_europe = 2.40053603985098E-14

    row_taiwan = pd.DataFrame({
        "Country": ["Taiwan"],
        "CF Nox": [cf_nox_asia],
        "CF NH3": [cf_nh3_asia],
        "CF Sox": [cf_sox_asia],
        "Country_Code": ["TW"],
    })
    row_malta = pd.DataFrame({
        "Country": ["Malta"],
        "CF Nox": [cf_nox_europe],
        "CF NH3": [cf_nh3_europe],
        "CF Sox": [cf_sox_europe],
        "Country_Code": ["MT"],
    })
    lci_acidification = pd.concat([lci_acidification, row_malta], ignore_index=True)
    lci_acidification = pd.concat([lci_acidification, row_taiwan], ignore_index=True)
    return lci_acidification

def region_to_country(row_countries):
    """
    Returns a map of regions to countries.
    """
    # Load the country mappings from arguments.json
    with open("pipeline/arguments.json", "r") as f:
        args = json.load(f)
    
    row_eu_countries = args["row_region_mappings"]["row_eu"]
    row_asia_pacific_countries = args["row_region_mappings"]["row_asia_pacific"]
    row_african_countries = args["row_region_mappings"]["row_africa"]
    row_american_countries = args["row_region_mappings"]["row_america"]
    row_middle_eastern_countries = args["row_region_mappings"]["row_middle_east"]

    region_to_country_map = {
        "WE": [],
        "WA": [],
        "WF": [],
        "WL": [],
        "WM": [],
    }
    for country in row_countries:
        if country in row_eu_countries.keys():
            region_to_country_map["WE"].append(row_eu_countries[country])
        elif country in row_asia_pacific_countries.keys():
            region_to_country_map["WA"].append(row_asia_pacific_countries[country])
        elif country in row_african_countries.keys():
            region_to_country_map["WF"].append(row_african_countries[country])
        elif country in row_american_countries.keys():
            region_to_country_map["WL"].append(row_american_countries[country])
        elif country in row_middle_eastern_countries.keys():
            region_to_country_map["WM"].append(row_middle_eastern_countries[country])
        else:
            print(f"Country {country} not found in any mapping, skipping.")
    
    return region_to_country_map

if __name__ == "__main__":
    # STEP 1: LOAD DATA
    # Load arguments from arguments.json
    with open("pipeline/arguments.json", "r") as f:
        args = json.load(f)
    
    lci_path = args["lc_impact_path"]  # Get path from arguments.json
    lci_climate, lci_ozone, lci_acidification, lci_freshwater_eutrophication, lci_marine_eutrophication, lci_land, lci_water = load_lci(lci_path)
    exio19_path = args["exio_19_path"]  # Get path from arguments.json
    # use caching to avoid loading regions every time
    try:
        with open("exio3_19_regions.txt", "r") as f:
            regions = f.read().splitlines()
    except FileNotFoundError:
        # if not, get the regions from the exio3_19 object and write them to the file
        exio3_19 = pymrio.parse_exiobase3(path=exio19_path)
        regions = exio3_19.get_regions()
        # write the regions to the file
        with open("exio3_19_regions.txt", "w") as f:
            for region in regions:
                f.write(f"{region}\n")
    print("Regions loaded from file:", regions)

    # STEP 2: ADD ALPHA-2 CODES TO LCI DATA
    lci_ozone["Country_Code"] = lci_ozone["Country"].apply(get_country_code)
    lci_acidification["Country_Code"] = lci_acidification["Country"].apply(get_country_code)
    lci_freshwater_eutrophication["Country_Code"] = lci_freshwater_eutrophication["Country"].apply(get_country_code)
    lci_marine_eutrophication["Country_Code"] = lci_marine_eutrophication["Country"].apply(get_country_code)
    lci_land["Country_Code"] = lci_land["Country"].apply(get_country_code)
    lci_water["Country_Code"] = lci_water["Country"].apply(get_country_code)
    # drop countries without alpha-2 code
    lci_ozone.dropna(subset=["Country_Code"], inplace=True)
    lci_acidification.dropna(subset=["Country_Code"], inplace=True)
    lci_freshwater_eutrophication.dropna(subset=["Country_Code"], inplace=True)
    lci_marine_eutrophication.dropna(subset=["Country_Code"], inplace=True)
    lci_land.dropna(subset=["Country_Code"], inplace=True)
    lci_water.dropna(subset=["Country_Code"], inplace=True)

    # STEP 3: GET ROW REGIONS (REGIONS NOT IN EXIOBASE) FOR EACH IMPACT CATEGORY
    row_ozone = get_row_regions(lci_ozone["Country_Code"].tolist(), regions)
    row_acidification = get_row_regions(lci_acidification["Country_Code"].tolist(), regions)
    row_freshwater_eutrophication = get_row_regions(lci_freshwater_eutrophication["Country_Code"].tolist(), regions)
    row_marine_eutrophication = get_row_regions(lci_marine_eutrophication["Country_Code"].tolist(), regions)
    row_land = get_row_regions(lci_land["Country_Code"].tolist(), regions)
    row_water = get_row_regions(lci_water["Country_Code"].tolist(), regions)
    print("Row regions for ozone:", row_ozone)
    print("Row regions for acidification:", row_acidification)
    print("Row regions for freshwater eutrophication:", row_freshwater_eutrophication)
    print("Row regions for marine eutrophication:", row_marine_eutrophication)
    print("Row regions for land use:", row_land)
    print("Row regions for water use:", row_water)

    # STEP 4: AUGMENT LCI DATA TO INCLUDE ALL EXIOBASE REGIONS BY USING CONTINENTAL AVERAGES
    row_regions = {
        "WA": "Asia and pacific",
        "WE": "Europe",
        "WF": "Africa",
        "WM": "Middle east",
        "WL": "America"
    }
    exio_regions_without_row = [region for region in regions if region not in row_regions.keys()]
    print(len(exio_regions_without_row)) # exiobase contains 44 exact regions + 5 row regions
    
    if (len(get_missing_from_lci(exio_regions_without_row, lci_ozone)) > 0):
        print("Missing from LCI ozone:", get_missing_from_lci(exio_regions_without_row, lci_ozone))
        # no augmentation for ozone since it is already complete
        assert len(get_missing_from_lci(exio_regions_without_row, lci_ozone)) == 0, "There are still missing regions in ozone after augmentation"

    if (len(get_missing_from_lci(exio_regions_without_row, lci_acidification)) > 0):
        print("Missing from LCI acidification:", get_missing_from_lci(exio_regions_without_row, lci_acidification))
        lci_acidification = augment_acid(lci_acidification)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_acidification)) == 0, "There are still missing regions in acidification after augmentation"

    if (len(get_missing_from_lci(exio_regions_without_row, lci_freshwater_eutrophication)) > 0):
        print("Missing from LCI freshwater eutrophication:", get_missing_from_lci(exio_regions_without_row, lci_freshwater_eutrophication))
        lci_freshwater_eutrophication = augment_freshwater(lci_freshwater_eutrophication)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_freshwater_eutrophication)) == 0, "There are still missing regions in freshwater eutrophication after augmentation"

    if (len(get_missing_from_lci(exio_regions_without_row, lci_marine_eutrophication)) > 0):
        print("Missing from LCI marine eutrophication:", get_missing_from_lci(exio_regions_without_row, lci_marine_eutrophication))
        lci_marine_eutrophication = augment_marine(lci_marine_eutrophication)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_marine_eutrophication)) == 0, "There are still missing regions in marine eutrophication after augmentation"

    if (len(get_missing_from_lci(exio_regions_without_row, lci_land)) > 0):
        print("Missing from LCI land use:", get_missing_from_lci(exio_regions_without_row, lci_land))
        lci_land = augment_land(lci_land)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_land)) == 0, "There are still missing regions in land use after augmentation"

    if (len(get_missing_from_lci(exio_regions_without_row, lci_water)) > 0):
        print("Missing from LCI water use:", get_missing_from_lci(exio_regions_without_row, lci_water))
        lci_water = augment_water(lci_water)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_water)) == 0, "There are still missing regions in water use after augmentation"

    # STEP 5: CATEGORIZE REGIONS TO CONTINENTAL GROUPS
    region_to_country_ozone = region_to_country(row_ozone)
    region_to_country_acidification = region_to_country(row_acidification)
    region_to_country_freshwater_eutrophication = region_to_country(row_freshwater_eutrophication)
    region_to_country_marine_eutrophication = region_to_country(row_marine_eutrophication)
    region_to_country_land = region_to_country(row_land)
    region_to_country_water = region_to_country(row_water)
