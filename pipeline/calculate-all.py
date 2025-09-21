import pymrio
import numpy as np
import pandas as pd
import pycountry as pyc
import json
import argparse

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
    
    # Add country codes to all LCI datasets and remove missing ones
    lci_ozone["Country_Code"] = lci_ozone["Country"].apply(get_country_code)
    lci_acidification["Country_Code"] = lci_acidification["Country"].apply(get_country_code)
    lci_freshwater_eutrophication["Country_Code"] = lci_freshwater_eutrophication["Country"].apply(get_country_code)
    lci_marine_eutrophication["Country_Code"] = lci_marine_eutrophication["Country"].apply(get_country_code)
    lci_land["Country_Code"] = lci_land["Country"].apply(get_country_code)
    lci_water["Country_Code"] = lci_water["Country"].apply(get_country_code)
    
    # Drop countries without alpha-2 code
    lci_ozone.dropna(subset=["Country_Code"], inplace=True)
    lci_acidification.dropna(subset=["Country_Code"], inplace=True)
    lci_freshwater_eutrophication.dropna(subset=["Country_Code"], inplace=True)
    lci_marine_eutrophication.dropna(subset=["Country_Code"], inplace=True)
    lci_land.dropna(subset=["Country_Code"], inplace=True)
    lci_water.dropna(subset=["Country_Code"], inplace=True)
    
    # Add Augmented column to all LCI datasets (marking original data)
    lci_ozone['Augmented'] = 'original'
    lci_acidification['Augmented'] = 'original'
    lci_freshwater_eutrophication['Augmented'] = 'original'
    lci_marine_eutrophication['Augmented'] = 'original'
    lci_land['Augmented'] = 'original'
    lci_water['Augmented'] = 'original'
    
    return lci_climate, lci_ozone, lci_acidification, lci_freshwater_eutrophication, lci_marine_eutrophication, lci_land, lci_water


def calculate_cba(exio3_11, diag_stressor, L):
    print(f"Calculating CBA for {diag_stressor.name}")
    diag_stressor.S = pymrio.calc_S(diag_stressor.F, exio3_11.x)
    Y_agg = exio3_11.Y.groupby(level="region", axis=1, sort=False).sum()
    diag_stressor.D_cba, _, _, _ = pymrio.calc_accounts(diag_stressor.S, L, Y_agg)
    return diag_stressor.D_cba


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
    if duplicates:
        print("Duplicates found in row regions:", duplicates)
    return unique_regions


def dr_s(D_cba):
    print("Calculating dr_s")
    columns = {}
    for series_name, series in D_cba.items():
        series_sum = series.sum()
        columns[series_name] = series / series_sum
    dr_s = pd.DataFrame(columns)
    return dr_s

def dr_u(dr_s, row_region_mappings, row_countries):
    print("Calculating dr_u")
    # Get region mappings from arguments
    row_eu_countries = row_region_mappings["row_eu"]
    row_asia_pacific_countries = row_region_mappings["row_asia_pacific"]
    row_african_countries = row_region_mappings["row_africa"]
    row_american_countries = row_region_mappings["row_america"]
    row_middle_eastern_countries = row_region_mappings["row_middle_east"]

    row_regions = {
        "WA": "Asia and pacific",
        "WE": "Europe",
        "WF": "Africa",
        "WM": "Middle east",
        "WL": "America"
    }

    # augment dr_s to create dr_u
    # new regions are calculated by dividing their corresponding row region by the number of countries in the row region
    # for example, row region Argentina is sub-matrix WA divided by the number of countries in row region WA
    wl = dr_s.loc["WL"].copy()
    wl = wl / len(row_american_countries)

    we = dr_s.loc["WE"].copy()
    we = we / len(row_eu_countries)

    wa = dr_s.loc["WA"].copy()
    wa = wa / len(row_asia_pacific_countries)

    wf = dr_s.loc["WF"].copy()
    wf = wf / len(row_african_countries)

    wm = dr_s.loc["WM"].copy()
    wm = wm / len(row_middle_eastern_countries)

    dr_u = dr_s.copy()
    dr_u = dr_u.drop(index=list(row_regions.keys()), level='region')

    # build a mapping of country codes to region dataframes - only for row countries 
    country_to_region = {}
    for region in row_countries:
        if region in row_eu_countries:
            country_to_region[region] = we
        elif region in row_asia_pacific_countries:
            country_to_region[region] = wa
        elif region in row_african_countries:
            country_to_region[region] = wf
        elif region in row_american_countries:
            country_to_region[region] = wl
        elif region in row_middle_eastern_countries:
            country_to_region[region] = wm
        else:
            print(f"Country {region} not found in any mapping, skipping.")

    # add all new regions that don't exist in exiobase to dr_u
    all_indices = []
    all_data = []
    for region in row_countries:
        if region in country_to_region:  # Only add if we found a mapping
            region_data = country_to_region[region].copy()
            idx = pd.MultiIndex.from_product([[region],region_data.index], names=['region', 'sector'])
            all_indices.append(idx)
            all_data.append(region_data)
        else:
            print(f"ERROR: Region %s not found in country to region map, this should not happen", region)

    combined_idx = pd.MultiIndex.from_tuples(
        [idx for subidx in all_indices for idx in subidx]
    )

    combined_data = pd.concat(all_data)
    combined_data.index = combined_idx

    dr_u = pd.concat([dr_u, combined_data])

    # remove row regions from consumption regions (columns)
    dr_u = dr_u.drop(columns=row_regions.keys(), axis=1, level=0)
    return dr_u


def dr_f(satellite, dr_u, stressor_name):
    print(f"Calculating dr_f for {stressor_name}")
    # use 2019 impact factors for calculating dr_f
    # calculate dr_f - share of the driver of biodiversity loss in impact region i from the total amount of the driver that is driven by consumption in consumption region j, product sector k
    dr_f = dr_u.copy()
    row_regions = {
        "WA": "Asia and pacific",
        "WE": "Europe",
        "WF": "Africa",
        "WM": "Middle east",
        "WL": "America"
    }
    satellite_cleaned = satellite.M.drop(columns=row_regions.keys(), axis=1, level=0)
    total = satellite_cleaned.loc[stressor_name]
    scalars = total.to_numpy() # multipliers for each column

    # multiply each column of dr_u by the respective column value from exio3_19 impact factors
    dr_f = dr_f * scalars # same as dr_f * diag(scalars) but more efficient with numpy broadcasting
    return dr_f


def pdf(lci, dr_f, stressor_name):
    print(f"Calculating PDF/€ {stressor_name}")
    # Country codes should already be added in load_lci function
    # Make a copy to avoid modifying the original dataframe
    lci_copy = lci.copy()
    lci_copy.set_index("Country_Code", inplace=True)
    # Ensure lci index is unique before reindexing
    lci_copy = lci_copy[~lci_copy.index.duplicated(keep='first')]
    # sort rows on lci in same order as dr_f.index.sortlevel
    lci_reindexed = lci_copy.reindex(dr_f.index.get_level_values(0).unique())

    # build array from the relevent lci stressor
    # every value should be repeated 200 times (number of sectors)
    cf = lci_reindexed[stressor_name].to_numpy()
    cf = np.repeat(cf, 200) # 1D array of length 200 * number of regions in lci
    # expand cf_all_effects to match the shape of dr_f
    cf = np.tile(cf, (dr_f.shape[1], 1)).T

    pdf = dr_f * cf
    pdf_total = pdf.sum()
    return pdf_total


def ozone_formation(lci_ozone, exio3_19, exio3_11, row_region_mappings, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ ozone formation")
    
    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Get row regions for ozone
    row_ozone = get_row_regions(lci_ozone["Country_Code"].tolist(), exio_regions)
    print("Row regions for ozone:", row_ozone)
    
    nmvoc_diag = exio3_11.satellite.diag_stressor(("NMVOC - combustion - air"))
    nox_diag = exio3_11.satellite.diag_stressor(("NOx - combustion - air"))

    D_cba_nmvoc = calculate_cba(exio3_11, nmvoc_diag, exio3_11.L)
    D_cba_nox = calculate_cba(exio3_11, nox_diag, exio3_11.L)

    dr_s_nmvoc = dr_s(D_cba_nmvoc)
    dr_s_nox = dr_s(D_cba_nox)

    dr_u_nmvoc = dr_u(dr_s_nmvoc, row_region_mappings, row_ozone)
    dr_u_nox = dr_u(dr_s_nox, row_region_mappings, row_ozone)

    dr_f_nmvoc = dr_f(exio3_19.satellite, dr_u_nmvoc, "NMVOC - combustion - air")
    dr_f_nox = dr_f(exio3_19.satellite, dr_u_nox, "NOx - combustion - air")

    # Save matrices if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-ozone-nmvoc.pkl", "wb") as f:
            pickle.dump(dr_f_nmvoc, f)
        with open("pipeline/output/matrices/pdf-matrix-ozone-nox.pkl", "wb") as f:
            pickle.dump(dr_f_nox, f)

    # Save CFs if enabled
    if store_cfs:
        # Store NMVOC CFs
        cf_nmvoc = lci_ozone[["Country_Code", "NMVOC", "Augmented"]].copy()
        cf_nmvoc.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_nmvoc.to_csv("pipeline/output/cfs/cfs-ozone-nmvoc.csv", index=False)
        
        # Store NOx CFs
        cf_nox = lci_ozone[["Country_Code", "NOx", "Augmented"]].copy()
        cf_nox.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_nox.to_csv("pipeline/output/cfs/cfs-ozone-nox.csv", index=False)

    ozone_nmvoc = pdf(lci_ozone, dr_f_nmvoc, "NMVOC")
    ozone_nox = pdf(lci_ozone, dr_f_nox, "NOx")

    return ozone_nmvoc, ozone_nox


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

    # Add Augmented column if it doesn't exist
    if 'Augmented' not in lci_acidification.columns:
        lci_acidification['Augmented'] = 'original'

    row_taiwan = pd.DataFrame({
        "Country": ["Taiwan"],
        "CF Nox": [cf_nox_asia],
        "CF NH3": [cf_nh3_asia],
        "CF Sox": [cf_sox_asia],
        "Country_Code": ["TW"],
        "Augmented": ["continental average (asia)"],
    })
    row_malta = pd.DataFrame({
        "Country": ["Malta"],
        "CF Nox": [cf_nox_europe],
        "CF NH3": [cf_nh3_europe],
        "CF Sox": [cf_sox_europe],
        "Country_Code": ["MT"],
        "Augmented": ["continental average (europe)"],
    })
    lci_acidification = pd.concat([lci_acidification, row_malta], ignore_index=True)
    lci_acidification = pd.concat([lci_acidification, row_taiwan], ignore_index=True)
    return lci_acidification


def acidification(lci_acidification, exio3_19, exio3_11, row_region_mappings, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ acidification")
    
    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    # Check if acidification data needs augmentation
    if len(get_missing_from_lci(exio_regions_without_row, lci_acidification)) > 0:
        print("Missing from LCI acidification:", get_missing_from_lci(exio_regions_without_row, lci_acidification))
        lci_acidification = augment_acid(lci_acidification)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_acidification)) == 0, "There are still missing regions in acidification after augmentation"
    
    # Get row regions for acidification
    row_acidification = get_row_regions(lci_acidification["Country_Code"].tolist(), exio_regions)
    print("Row regions for acidification:", row_acidification)
    
    nox_diag = exio3_11.satellite.diag_stressor(("NOx - combustion - air"))
    nh3_diag = exio3_11.satellite.diag_stressor(("NH3 - agriculture - air"))
    sox_diag = exio3_11.satellite.diag_stressor(("SOx - combustion - air"))

    D_cba_nox = calculate_cba(exio3_11, nox_diag, exio3_11.L)
    D_cba_nh3 = calculate_cba(exio3_11, nh3_diag, exio3_11.L)
    D_cba_sox = calculate_cba(exio3_11, sox_diag, exio3_11.L)

    dr_s_nox = dr_s(D_cba_nox)
    dr_s_nh3 = dr_s(D_cba_nh3)
    dr_s_sox = dr_s(D_cba_sox)

    dr_u_nox = dr_u(dr_s_nox, row_region_mappings, row_acidification)
    dr_u_nh3 = dr_u(dr_s_nh3, row_region_mappings, row_acidification)
    dr_u_sox = dr_u(dr_s_sox, row_region_mappings, row_acidification)

    dr_f_nox = dr_f(exio3_19.satellite, dr_u_nox, "NOx - combustion - air")
    dr_f_nh3 = dr_f(exio3_19.satellite, dr_u_nh3, "NH3 - agriculture - air")
    dr_f_sox = dr_f(exio3_19.satellite, dr_u_sox, "SOx - combustion - air")

    # Save matrices if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-acidification-nox.pkl", "wb") as f:
            pickle.dump(dr_f_nox, f)
        with open("pipeline/output/matrices/pdf-matrix-acidification-nh3.pkl", "wb") as f:
            pickle.dump(dr_f_nh3, f)
        with open("pipeline/output/matrices/pdf-matrix-acidification-sox.pkl", "wb") as f:
            pickle.dump(dr_f_sox, f)

    # Save CFs if enabled
    if store_cfs:
        # Store NOx CFs
        cf_nox = lci_acidification[["Country_Code", "CF Nox", "Augmented"]].copy()
        cf_nox.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_nox.to_csv("pipeline/output/cfs/cfs-acidification-nox.csv", index=False)
        
        # Store NH3 CFs
        cf_nh3 = lci_acidification[["Country_Code", "CF NH3", "Augmented"]].copy()
        cf_nh3.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_nh3.to_csv("pipeline/output/cfs/cfs-acidification-nh3.csv", index=False)
        
        # Store SOx CFs
        cf_sox = lci_acidification[["Country_Code", "CF Sox", "Augmented"]].copy()
        cf_sox.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_sox.to_csv("pipeline/output/cfs/cfs-acidification-sox.csv", index=False)

    acidification_nox = pdf(lci_acidification, dr_f_nox, "CF Nox")
    acidification_nh3 = pdf(lci_acidification, dr_f_nh3, "CF NH3")
    acidification_sox = pdf(lci_acidification, dr_f_sox, "CF Sox")

    return acidification_nox, acidification_nh3, acidification_sox


def augment_land(lci_land):
    # taiwan is missing from lc-impact, add taiwan as new row with country code TW and asia averages
    cf_annual_asia = 1.4159650959661E-15
    cf_permanent_asia = 1.02741974515257E-15
    cf_forestry_extensive_asia = 7.54516069592159E-16
    cf_forestry_intensive_asia = 2.78433669846512E-15
    cf_forestry_asia = (cf_forestry_extensive_asia + cf_forestry_intensive_asia) / 2
    cf_urban_asia = 1.64333114974599E-15
    cf_average_asia = (cf_annual_asia + cf_permanent_asia) / 2
    
    # Add Augmented column if it doesn't exist
    if 'Augmented' not in lci_land.columns:
        lci_land['Augmented'] = 'original'
    
    row = pd.DataFrame({
        "Country": ["Taiwan"],
        "Average": [cf_average_asia],
        "Annual crops Median": [cf_annual_asia],
        "Permanent crops Median": [cf_permanent_asia],
        "Pasture Median": [cf_annual_asia],
        "Forestry Median": [cf_forestry_asia],
        "Urban Median": [cf_urban_asia],
        "Country_Code": ["TW"],
        "Augmented": ["continental average (asia)"],
    })
    lci_land = pd.concat([lci_land, row], ignore_index=True)
    return lci_land


def land_annual_permanent(lci_land, exio3_11, exio3_19, row_region_mappings, exiobase_grouping_patterns, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ land use (annual and permanent crops)")

    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    if (len(get_missing_from_lci(exio_regions_without_row, lci_land)) > 0):
        print("Missing from LCI land use:", get_missing_from_lci(exio_regions_without_row, lci_land))
        lci_land = augment_land(lci_land)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_land)) == 0, "There are still missing regions in land use after augmentation"
    
    # Get row regions
    row_land = get_row_regions(lci_land["Country_Code"].tolist(), exio_regions)
    print("Row regions for land use:", row_land)
    
    # Annual / permanent crops
    groups = exio3_11.satellite.get_index(
        as_dict=True,
        grouping_pattern=exiobase_grouping_patterns["land_annual_permanent"]
    )

    exio3_11.satellite_agg = exio3_11.satellite.copy(new_name="Aggregated land stress - annual and permanent")

    for df_name, df in zip(exio3_11.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_11.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()

    groups = exio3_19.satellite.get_index(
        as_dict=True,
        grouping_pattern=exiobase_grouping_patterns["land_annual_permanent"]
    )

    exio3_19.satellite_agg = exio3_19.satellite.copy(new_name="Aggregated land stress - annual and permanent")

    for df_name, df in zip(exio3_19.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_19.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()

    annual_diag = exio3_11.satellite_agg.diag_stressor("Land stress - annual and permanent")
    D_cba_annual = calculate_cba(exio3_11, annual_diag, exio3_11.L)
    dr_s_annual = dr_s(D_cba_annual)
    dr_u_annual = dr_u(dr_s_annual, row_region_mappings, row_land)
    dr_f_annual = dr_f(exio3_19.satellite_agg, dr_u_annual, 'Land stress - annual and permanent')
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-land-annual-permanent-crops.pkl", "wb") as f:
            pickle.dump(dr_f_annual, f)

    # Save CFs if enabled
    if store_cfs:
        # Store permanent crops CFs
        cf_permanent = lci_land[["Country_Code", "Permanent crops Median", "Augmented"]].copy()
        cf_permanent.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_permanent.to_csv("pipeline/output/cfs/cfs-land-permanent.csv", index=False)
    
    land_annual_permanent_crops = pdf(lci_land, dr_f_annual, "Permanent crops Median")

    return land_annual_permanent_crops


def land_annual(lci_land, exio3_11, exio3_19, row_region_mappings, exiobase_grouping_patterns, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ land use (annual crops)")

    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    if (len(get_missing_from_lci(exio_regions_without_row, lci_land)) > 0):
        print("Missing from LCI land use:", get_missing_from_lci(exio_regions_without_row, lci_land))
        lci_land = augment_land(lci_land)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_land)) == 0, "There are still missing regions in land use after augmentation"
    
    # Get row regions
    row_land = get_row_regions(lci_land["Country_Code"].tolist(), exio_regions)
    print("Row regions for land use:", row_land)
    
    # Annual crops
    groups = exio3_11.satellite.get_index(
        as_dict=True,
        grouping_pattern=exiobase_grouping_patterns["land_annual"]
    )

    exio3_11.satellite_agg = exio3_11.satellite.copy(new_name="Aggregated land stress - annual crops")

    for df_name, df in zip(exio3_11.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_11.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()

    groups = exio3_19.satellite.get_index(
        as_dict=True,
        grouping_pattern=exiobase_grouping_patterns["land_annual"]
    )

    exio3_19.satellite_agg = exio3_19.satellite.copy(new_name="Aggregated land stress - annual crops")

    for df_name, df in zip(exio3_19.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_19.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()
    
    annual_diag = exio3_11.satellite_agg.diag_stressor("Land stress - annual crops")
    D_cba_annual = calculate_cba(exio3_11, annual_diag, exio3_11.L)
    dr_s_annual = dr_s(D_cba_annual)
    dr_u_annual = dr_u(dr_s_annual, row_region_mappings, row_land)
    dr_f_annual = dr_f(exio3_19.satellite_agg, dr_u_annual, "Land stress - annual crops")
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-land-annual-crops.pkl", "wb") as f:
            pickle.dump(dr_f_annual, f)

    # Save CFs if enabled
    if store_cfs:
        # Store annual crops CFs
        cf_annual = lci_land[["Country_Code", "Annual crops Median", "Augmented"]].copy()
        cf_annual.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_annual.to_csv("pipeline/output/cfs/cfs-land-annual.csv", index=False)
    
    land_annual_crops = pdf(lci_land, dr_f_annual, "Annual crops Median")

    return land_annual_crops


def land_pasture(lci_land, exio3_11, exio3_19, row_region_mappings, exiobase_grouping_patterns, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ land use (pasture)")

    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    if (len(get_missing_from_lci(exio_regions_without_row, lci_land)) > 0):
        print("Missing from LCI land use:", get_missing_from_lci(exio_regions_without_row, lci_land))
        lci_land = augment_land(lci_land)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_land)) == 0, "There are still missing regions in land use after augmentation"
    
    # Get row regions
    row_land = get_row_regions(lci_land["Country_Code"].tolist(), exio_regions)
    print("Row regions for land use:", row_land)

    # Pasture
    groups = exio3_11.satellite.get_index(
        as_dict=True,
        grouping_pattern=exiobase_grouping_patterns["land_pasture"]
    )

    exio3_11.satellite_agg = exio3_11.satellite.copy(new_name="Aggregated land stress - pasture")

    for df_name, df in zip(exio3_11.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_11.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()

    groups = exio3_19.satellite.get_index(
        as_dict=True,
        grouping_pattern=exiobase_grouping_patterns["land_pasture"]
    )

    exio3_19.satellite_agg = exio3_19.satellite.copy(new_name="Aggregated land stress - pasture")

    for df_name, df in zip(exio3_19.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_19.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()
    
    pasture_diag = exio3_11.satellite_agg.diag_stressor("Land stress - pasture")
    D_cba_pasture = calculate_cba(exio3_11, pasture_diag, exio3_11.L)
    dr_s_pasture = dr_s(D_cba_pasture)
    dr_u_pasture = dr_u(dr_s_pasture, row_region_mappings, row_land)
    dr_f_pasture = dr_f(exio3_19.satellite_agg, dr_u_pasture, "Land stress - pasture")
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-land-pasture.pkl", "wb") as f:
            pickle.dump(dr_f_pasture, f)

    # Save CFs if enabled
    if store_cfs:
        # Store pasture CFs
        cf_pasture = lci_land[["Country_Code", "Pasture Median", "Augmented"]].copy()
        cf_pasture.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_pasture.to_csv("pipeline/output/cfs/cfs-land-pasture.csv", index=False)
    
    land_pasture = pdf(lci_land, dr_f_pasture, "Pasture Median")

    return land_pasture


def land_forestry(lci_land, exio3_11, exio3_19, row_region_mappings, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ land use (forestry)")

    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    if (len(get_missing_from_lci(exio_regions_without_row, lci_land)) > 0):
        print("Missing from LCI land use:", get_missing_from_lci(exio_regions_without_row, lci_land))
        lci_land = augment_land(lci_land)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_land)) == 0, "There are still missing regions in land use after augmentation"
    
    # Get row regions
    row_land = get_row_regions(lci_land["Country_Code"].tolist(), exio_regions)
    print("Row regions for land use:", row_land)

    # Forestry
    forestry_diag = exio3_11.satellite.diag_stressor(("Forest area - Forestry"))
    D_cba_forestry = calculate_cba(exio3_11, forestry_diag, exio3_11.L)
    dr_s_forestry = dr_s(D_cba_forestry)
    dr_u_forestry = dr_u(dr_s_forestry, row_region_mappings, row_land)
    dr_f_forestry = dr_f(exio3_19.satellite, dr_u_forestry, "Forest area - Forestry")
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-land-forestry.pkl", "wb") as f:
            pickle.dump(dr_f_forestry, f)

    # Save CFs if enabled
    if store_cfs:
        # Store forestry CFs
        cf_forestry = lci_land[["Country_Code", "Forestry Median", "Augmented"]].copy()
        cf_forestry.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_forestry.to_csv("pipeline/output/cfs/cfs-land-forestry.csv", index=False)
    
    land_forestry = pdf(lci_land, dr_f_forestry, "Forestry Median")

    return land_forestry


def land_other(lci_land, exio3_11, exio3_19, row_region_mappings, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ land use (other/urban)")

    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    if (len(get_missing_from_lci(exio_regions_without_row, lci_land)) > 0):
        print("Missing from LCI land use:", get_missing_from_lci(exio_regions_without_row, lci_land))
        lci_land = augment_land(lci_land)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_land)) == 0, "There are still missing regions in land use after augmentation"
    
    # Get row regions
    row_land = get_row_regions(lci_land["Country_Code"].tolist(), exio_regions)
    print("Row regions for land use:", row_land)

    # Other land use (urban)
    other_diag = exio3_11.satellite.diag_stressor(("Other land Use: Total"))
    D_cba_other = calculate_cba(exio3_11, other_diag, exio3_11.L)
    dr_s_other = dr_s(D_cba_other)
    dr_u_other = dr_u(dr_s_other, row_region_mappings, row_land)
    dr_f_other = dr_f(exio3_19.satellite, dr_u_other, "Other land Use: Total")
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-land-other.pkl", "wb") as f:
            pickle.dump(dr_f_other, f)

    # Save CFs if enabled
    if store_cfs:
        # Store urban/other land use CFs
        cf_urban = lci_land[["Country_Code", "Urban Median", "Augmented"]].copy()
        cf_urban.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_urban.to_csv("pipeline/output/cfs/cfs-land-urban.csv", index=False)
    
    land_other = pdf(lci_land, dr_f_other, "Urban Median")

    return land_other


def climate_change(lci_climate, exio3_19, exiobase_grouping_patterns, store_cfs=False):
    print("Calculating PDF/€ climate change")

    # TODO: this grouping should be checked
    groups = exio3_19.satellite.get_index(as_dict=True, grouping_pattern=exiobase_grouping_patterns["climate_change"])

    satellite_agg = exio3_19.satellite.copy()

    for df_name, df in zip(satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            satellite_agg.__dict__[df_name] = df.groupby(groups).sum()


    # TODO: check if using 'all effects 100yrs' is correct
    # calculate aquatic factors
    climate_aquatic = satellite_agg.M.loc['CO2 - Total'] * lci_climate['All effects 100yrs (aquatic)'].values[0] + \
               satellite_agg.M.loc['CH4'] * lci_climate['All effects 100yrs (aquatic)'].values[1] + \
               satellite_agg.M.loc['CH4 fossil'] * lci_climate['All effects 100yrs (aquatic)'].values[2] + \
               satellite_agg.M.loc['NOx - Total'] * lci_climate['All effects 100yrs (aquatic)'].values[3]
    # calculate terrestrial factors
    climate_terrestrial = satellite_agg.M.loc['CO2 - Total'] * lci_climate['All effects 100yrs (terrestrial)'].values[0] + \
               satellite_agg.M.loc['CH4'] * lci_climate['All effects 100yrs (terrestrial)'].values[1] + \
               satellite_agg.M.loc['CH4 fossil'] * lci_climate['All effects 100yrs (terrestrial)'].values[2] + \
               satellite_agg.M.loc['NOx - Total'] * lci_climate['All effects 100yrs (terrestrial)'].values[3]
    
    # Save CFs if enabled
    if store_cfs:
        import pandas as pd
        # Climate CFs are substance-specific, not country-specific
        # Create 8 files: 4 aquatic + 4 terrestrial
        substances = ['CO2', 'CH4', 'CH4-fossil', 'NOx']
        
        # Aquatic CFs
        for i, substance in enumerate(substances):
            cf_data = pd.DataFrame({
                'Substance': [substance],
                'CF_Value': [lci_climate['All effects 100yrs (aquatic)'].values[i]],
                'Augmented': ['original']
            })
            cf_data.to_csv(f"pipeline/output/cfs/cfs-climate-aquatic-{substance.lower()}.csv", index=False)
        
        # Terrestrial CFs
        for i, substance in enumerate(substances):
            cf_data = pd.DataFrame({
                'Substance': [substance],
                'CF_Value': [lci_climate['All effects 100yrs (terrestrial)'].values[i]],
                'Augmented': ['original']
            })
            cf_data.to_csv(f"pipeline/output/cfs/cfs-climate-terrestrial-{substance.lower()}.csv", index=False)
    
    return climate_aquatic, climate_terrestrial


def augment_freshwater(lci_freshwater):
    # malta is missing from lc-impact, add malta as new row with country code MT and EU averages
    p_w_eu = 2.19740701963604E-13
    p_s_eu = 2.27816881528299E-14
    p_avg_eu = (p_w_eu + p_s_eu) / 2
    
    # Add Augmented column if it doesn't exist
    if 'Augmented' not in lci_freshwater.columns:
        lci_freshwater['Augmented'] = 'original'
    
    malta_row = pd.DataFrame({
        "Country": ["Malta"],
        "CF for P emissions to water [PDFyr/kg]": [p_w_eu],
        "CF for P emissions to soil [PDFyr/kg]": [p_s_eu],
        "Average": [p_avg_eu],
        "Country_Code": ["MT"],
        "Augmented": ["continental average (europe)"],
    })
    lci_freshwater = pd.concat([lci_freshwater, malta_row], ignore_index=True)
    # cyprus is missing from lc-impact, add cyprus as new row with country code CY and EU averages
    cyprus_row = pd.DataFrame({
        "Country": ["Cyprus"],
        "CF for P emissions to water [PDFyr/kg]": [p_w_eu],
        "CF for P emissions to soil [PDFyr/kg]": [p_s_eu],
        "Average": [p_avg_eu],
        "Country_Code": ["CY"],
        "Augmented": ["continental average (europe)"],
    })
    lci_freshwater = pd.concat([lci_freshwater, cyprus_row], ignore_index=True)
    return lci_freshwater


def augment_marine(lci_marine):
    n_w_eu = 3.86913531769129E-15
    
    # Add Augmented column if it doesn't exist
    if 'Augmented' not in lci_marine.columns:
        lci_marine['Augmented'] = 'original'
    
    luxembourg_row = pd.DataFrame({
        "Country": ["Luxembourg"],
        "Country_Code": ["LU"],
        "CF for direct N emission to marine system [PDF*yr/kg]": [n_w_eu],
        "Augmented": ["continental average (europe)"],
    })
    switzerland_row = pd.DataFrame({
        "Country": ["Switzerland"],
        "Country_Code": ["CH"],
        "CF for direct N emission to marine system [PDF*yr/kg]": [n_w_eu],
        "Augmented": ["continental average (europe)"],
    })
    lci_marine = pd.concat([lci_marine, luxembourg_row, switzerland_row], ignore_index=True)
    return lci_marine


def augment_water(lci_water):
    # malta is missing from lc-impact, add malta as new row with country code MT and EU averages
    cf_all_eu = 9.02E-15
    
    # Add Augmented column if it doesn't exist
    if 'Augmented' not in lci_water.columns:
        lci_water['Augmented'] = 'original'
    
    row = pd.DataFrame({
        "Country": ["Malta"],
        "CF all effects  [PDF·yr/m3]": [cf_all_eu],
        "Country_Code": ["MT"],
        "Augmented": ["continental average (europe)"],
    })
    lci_water = pd.concat([lci_water, row], ignore_index=True)
    return lci_water


def water_consumption(lci_water, exio3_19, exio3_11, row_region_mappings, exiobase_grouping_patterns, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ water consumption")
    
    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    # Check if water data needs augmentation
    if len(get_missing_from_lci(exio_regions_without_row, lci_water)) > 0:
        print("Missing from LCI water use:", get_missing_from_lci(exio_regions_without_row, lci_water))
        lci_water = augment_water(lci_water)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_water)) == 0, "There are still missing regions in water use after augmentation"
    
    # Get row regions for water consumption
    row_water = get_row_regions(lci_water["Country_Code"].tolist(), exio_regions)
    print("Row regions for water consumption:", row_water)
    
    # Aggregate all blue water consumption related drivers
    groups = exio3_11.satellite.get_index(as_dict=True, grouping_pattern=exiobase_grouping_patterns["water_consumption"])
    
    exio3_11.satellite_agg = exio3_11.satellite.copy(new_name="Aggregated blue water consumption accounts")
    
    for df_name, df in zip(exio3_11.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_11.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_11.satellite_agg.__dict__[df_name] = df.groupby(groups).sum()
    
    # Diagonalize aggregated blue water consumption
    water_diag = exio3_11.satellite_agg.diag_stressor(("Water Consumption Blue – Total"))

    D_cba_water = calculate_cba(exio3_11, water_diag, exio3_11.L)
    dr_s_water = dr_s(D_cba_water)
    dr_u_water = dr_u(dr_s_water, row_region_mappings, row_water)
    
    # Aggregate water consumption drivers for 2019 data
    groups_19 = exio3_19.satellite.get_index(as_dict=True, grouping_pattern=exiobase_grouping_patterns["water_consumption"])
    
    exio3_19.satellite_agg = exio3_19.satellite.copy(new_name="Aggregated blue water consumption accounts")
    
    for df_name, df in zip(exio3_19.satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    exio3_19.satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups_19).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            exio3_19.satellite_agg.__dict__[df_name] = df.groupby(groups_19).sum()
    
    # Calculate dr_f manually since we need to use aggregated satellite data
    print("Calculating dr_f for Water Consumption Blue – Total")
    dr_f_water = dr_f(exio3_19.satellite_agg, dr_u_water, "Water Consumption Blue – Total")
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-water-consumption.pkl", "wb") as f:
            pickle.dump(dr_f_water, f)

    # Save CFs if enabled
    if store_cfs:
        # Store water consumption CFs
        cf_water = lci_water[["Country_Code", "CF all effects  [PDF·yr/m3]", "Augmented"]].copy()
        cf_water.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_water.to_csv("pipeline/output/cfs/cfs-water-consumption.csv", index=False)
    
    water_total = pdf(lci_water, dr_f_water, "CF all effects  [PDF·yr/m3]")

    return water_total


def marine_eutrophication(lci_marine, exio3_19, exio3_11, row_region_mappings, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ marine eutrophication")
    
    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    # Check if marine data needs augmentation
    if len(get_missing_from_lci(exio_regions_without_row, lci_marine)) > 0:
        print("Missing from LCI marine eutrophication:", get_missing_from_lci(exio_regions_without_row, lci_marine))
        lci_marine = augment_marine(lci_marine)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_marine)) == 0, "There are still missing regions in marine eutrophication after augmentation"
    
    # Get row regions for marine eutrophication
    row_marine = get_row_regions(lci_marine["Country_Code"].tolist(), exio_regions)
    print("Row regions for marine eutrophication:", row_marine)
    
    # Calculate for nitrogen water emissions
    n_diag = exio3_11.satellite.diag_stressor(("N - agriculture - water"))

    D_cba_n = calculate_cba(exio3_11, n_diag, exio3_11.L)
    dr_s_n = dr_s(D_cba_n)
    dr_u_n = dr_u(dr_s_n, row_region_mappings, row_marine)
    dr_f_n = dr_f(exio3_19.satellite, dr_u_n, "N - agriculture - water")
    
    # Save matrix if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-marine-eutrophication.pkl", "wb") as f:
            pickle.dump(dr_f_n, f)

    # Save CFs if enabled
    if store_cfs:
        # Store N marine emission CFs
        cf_n_marine = lci_marine[["Country_Code", "CF for direct N emission to marine system [PDF*yr/kg]", "Augmented"]].copy()
        cf_n_marine.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_n_marine.to_csv("pipeline/output/cfs/cfs-marine-nitrogen.csv", index=False)
    
    marine_n = pdf(lci_marine, dr_f_n, "CF for direct N emission to marine system [PDF*yr/kg]")

    return marine_n


def freshwater_eutrophication(lci_freshwater, exio3_19, exio3_11, row_region_mappings, store_matrix=False, store_cfs=False):
    print("Calculating PDF/€ freshwater eutrophication")
    
    # Get EXIOBASE regions
    exio_regions = exio3_19.get_regions()
    
    # Define row regions (rest of world regions in EXIOBASE)
    row_regions = {"WA": "Asia and pacific", "WE": "Europe", "WF": "Africa", "WM": "Middle east", "WL": "America"}
    exio_regions_without_row = [region for region in exio_regions if region not in row_regions.keys()]
    
    # Check if freshwater data needs augmentation
    if len(get_missing_from_lci(exio_regions_without_row, lci_freshwater)) > 0:
        print("Missing from LCI freshwater eutrophication:", get_missing_from_lci(exio_regions_without_row, lci_freshwater))
        lci_freshwater = augment_freshwater(lci_freshwater)
        assert len(get_missing_from_lci(exio_regions_without_row, lci_freshwater)) == 0, "There are still missing regions in freshwater eutrophication after augmentation"
    
    # Get row regions for freshwater eutrophication
    row_freshwater = get_row_regions(lci_freshwater["Country_Code"].tolist(), exio_regions)
    print("Row regions for freshwater eutrophication:", row_freshwater)
    
    # Calculate for both phosphorus water and soil emissions
    p_water_diag = exio3_11.satellite.diag_stressor(("P - agriculture - water"))
    p_soil_diag = exio3_11.satellite.diag_stressor(("P - agriculture - soil"))

    D_cba_p_water = calculate_cba(exio3_11, p_water_diag, exio3_11.L)
    D_cba_p_soil = calculate_cba(exio3_11, p_soil_diag, exio3_11.L)
    
    dr_s_p_water = dr_s(D_cba_p_water)
    dr_s_p_soil = dr_s(D_cba_p_soil)
    
    dr_u_p_water = dr_u(dr_s_p_water, row_region_mappings, row_freshwater)
    dr_u_p_soil = dr_u(dr_s_p_soil, row_region_mappings, row_freshwater)
    
    dr_f_p_water = dr_f(exio3_19.satellite, dr_u_p_water, "P - agriculture - water")
    dr_f_p_soil = dr_f(exio3_19.satellite, dr_u_p_soil, "P - agriculture - soil")
    
    # Save matrices if enabled
    if store_matrix:
        import pickle
        with open("pipeline/output/matrices/pdf-matrix-freshwater-eutrophication-water.pkl", "wb") as f:
            pickle.dump(dr_f_p_water, f)
        with open("pipeline/output/matrices/pdf-matrix-freshwater-eutrophication-soil.pkl", "wb") as f:
            pickle.dump(dr_f_p_soil, f)

    # Save CFs if enabled
    if store_cfs:
        # Store P water emission CFs
        cf_p_water = lci_freshwater[["Country_Code", "CF for P emissions to water [PDFyr/kg]", "Augmented"]].copy()
        cf_p_water.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_p_water.to_csv("pipeline/output/cfs/cfs-freshwater-water.csv", index=False)
        
        # Store P soil emission CFs
        cf_p_soil = lci_freshwater[["Country_Code", "CF for P emissions to soil [PDFyr/kg]", "Augmented"]].copy()
        cf_p_soil.columns = ["Country_Code", "CF_Value", "Augmented"]
        cf_p_soil.to_csv("pipeline/output/cfs/cfs-freshwater-soil.csv", index=False)
    
    freshwater_p_water = pdf(lci_freshwater, dr_f_p_water, "CF for P emissions to water [PDFyr/kg]")
    freshwater_p_soil = pdf(lci_freshwater, dr_f_p_soil, "CF for P emissions to soil [PDFyr/kg]")

    return freshwater_p_water, freshwater_p_soil


def calculate_all(lci_path, exio_19_path, exio_11_path, row_region_mappings, exiobase_grouping_patterns, store_matrix=False, store_cfs=False):
    lci_climate, lci_ozone, lci_acidification, lci_freshwater_eutrophication, lci_marine_eutrophication, lci_land, lci_water = load_lci(lci_path)

    # Create matrices directory if store_matrix is True
    if store_matrix:
        import os
        matrices_dir = "pipeline/output/matrices"
        os.makedirs(matrices_dir, exist_ok=True)
        print(f"Matrix storage enabled. Matrices will be saved to {matrices_dir}")

    # Create CFs directory if store_cfs is True
    if store_cfs:
        import os
        cfs_dir = "pipeline/output/cfs"
        os.makedirs(cfs_dir, exist_ok=True)
        print(f"CFs storage enabled. Characterization factors will be saved to {cfs_dir}")

    # exiobase 2019 is used for impact factors
    exio3_19 = pymrio.parse_exiobase3(path=exio_19_path)
    # exiobase 2011 is used for calculating share of stressor for each region-product pair
    exio3_11 = pymrio.parse_exiobase3(path=exio_11_path)
    print("Calculating A (exio3_11)")
    exio3_11.A = pymrio.calc_A(exio3_11.Z, exio3_11.x)
    print("Calculating L (exio3_11)")
    exio3_11.L = pymrio.calc_L(exio3_11.A)

    # Calculate climate change impact
    climate_aquatic, climate_terrestrial = climate_change(lci_climate, exio3_19, exiobase_grouping_patterns, store_cfs)

    # Calculate ozone formation impact
    ozone_nmvoc, ozone_nox = ozone_formation(lci_ozone, exio3_19, exio3_11, row_region_mappings, store_matrix, store_cfs)
    
    # Calculate acidification impact
    acidification_nox, acidification_nh3, acidification_sox = acidification(lci_acidification, exio3_19, exio3_11, row_region_mappings, store_matrix, store_cfs)
    
    # Calculate freshwater eutrophication impact
    freshwater_p_water, freshwater_p_soil = freshwater_eutrophication(lci_freshwater_eutrophication, exio3_19, exio3_11, row_region_mappings, store_matrix, store_cfs)
    
    # Calculate marine eutrophication impact
    marine_n = marine_eutrophication(lci_marine_eutrophication, exio3_19, exio3_11, row_region_mappings, store_matrix, store_cfs)
    
    # Calculate water consumption impact
    water_total = water_consumption(lci_water, exio3_19, exio3_11, row_region_mappings, exiobase_grouping_patterns, store_matrix, store_cfs)
    
    # Calculate land use impact
    land_annual_permanent_impact = land_annual_permanent(lci_land, exio3_11, exio3_19, row_region_mappings, exiobase_grouping_patterns, store_matrix, store_cfs)
    land_annual_impact = land_annual(lci_land, exio3_11, exio3_19, row_region_mappings, exiobase_grouping_patterns, store_matrix, store_cfs)
    land_pasture_impact = land_pasture(lci_land, exio3_11, exio3_19, row_region_mappings, exiobase_grouping_patterns, store_matrix, store_cfs)
    land_forestry_impact = land_forestry(lci_land, exio3_11, exio3_19, row_region_mappings, store_matrix, store_cfs)
    land_other_impact = land_other(lci_land, exio3_11, exio3_19, row_region_mappings, store_matrix, store_cfs)

    # Write the results
    pd.DataFrame(climate_aquatic).to_csv("pipeline/output/pdf-climate-aquatic.csv", index=True)
    pd.DataFrame(climate_terrestrial).to_csv("pipeline/output/pdf-climate-terrestrial.csv", index=True)
    pd.DataFrame(ozone_nmvoc).to_csv("pipeline/output/pdf-ozone-nmvoc.csv", index=True)
    pd.DataFrame(ozone_nox).to_csv("pipeline/output/pdf-ozone-nox.csv", index=True)
    pd.DataFrame(acidification_nox).to_csv("pipeline/output/pdf-acidification-nox.csv", index=True)
    pd.DataFrame(acidification_nh3).to_csv("pipeline/output/pdf-acidification-nh3.csv", index=True)
    pd.DataFrame(acidification_sox).to_csv("pipeline/output/pdf-acidification-sox.csv", index=True)
    pd.DataFrame(freshwater_p_water).to_csv("pipeline/output/pdf-freshwater-eutrophication-water.csv", index=True)
    pd.DataFrame(freshwater_p_soil).to_csv("pipeline/output/pdf-freshwater-eutrophication-soil.csv", index=True)
    pd.DataFrame(marine_n).to_csv("pipeline/output/pdf-marine-eutrophication.csv", index=True)
    pd.DataFrame(water_total).to_csv("pipeline/output/pdf-water-consumption.csv", index=True)
    pd.DataFrame(land_annual_permanent_impact).to_csv("pipeline/output/pdf-land-annual-permanent-crops.csv", index=True)
    pd.DataFrame(land_annual_impact).to_csv("pipeline/output/pdf-land-annual-crops.csv", index=True)
    pd.DataFrame(land_pasture_impact).to_csv("pipeline/output/pdf-land-pasture.csv", index=True)
    pd.DataFrame(land_forestry_impact).to_csv("pipeline/output/pdf-land-forestry.csv", index=True)
    pd.DataFrame(land_other_impact).to_csv("pipeline/output/pdf-land-other.csv", index=True)


def main():
    parser = argparse.ArgumentParser(description="Calculate PDF (Probability of Disappearance of Fractions) values for various environmental impact categories.")
    parser.add_argument("json_file", type=str, help="Path to the JSON file containing configuration parameters.")
    parser.add_argument("--store-matrix", action="store_true", 
                        help="Store dr_f matrices as pickle files to output/matrices directory. "
                             "These matrices contain the regional distribution of environmental impacts "
                             "per euro spent. Climate impact matrices are not stored as they are not "
                             "regionally distributed.")
    parser.add_argument("--store-cfs", action="store_true",
                        help="Store characterization factors as CSV files to output/cfs directory. "
                             "These files contain the CF values used in calculations with country codes "
                             "and augmentation source information for transparency.")
    
    # Parse the arguments
    args = parser.parse_args()
    json_file = args.json_file
    store_matrix = args.store_matrix
    store_cfs = args.store_cfs

    try:
        # Open and read the JSON file
        with open(json_file, 'r') as file:
            data = json.load(file)
        
        # Print the parsed JSON data
        print("Successfully parsed JSON file:")
        print(json.dumps(data, indent=4))  # Pretty-print JSON

        calculate_all(data['lc_impact_path'], data['exio_19_path'], data['exio_11_path'], data['row_region_mappings'], data['exiobase_grouping_patterns'], store_matrix, store_cfs)
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON file. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
