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
    return lci_climate, lci_ozone, lci_acidification, lci_freshwater_eutrophication, lci_marine_eutrophication, lci_land, lci_water


def calculate_cba(exio3_11, diag_stressor, L):
    print(f"Calculating CBA for {diag_stressor.name}")
    diag_stressor.S = pymrio.calc_S(diag_stressor.F, exio3_11.x)
    Y_agg = exio3_11.Y.groupby(level="region", axis=1, sort=False).sum()
    diag_stressor.D_cba, _, _, _ = pymrio.calc_accounts(diag_stressor.S, L, Y_agg)
    return diag_stressor.D_cba


def get_country_code(name):
    extra_mappings = {
        "Turkey": "TR",
        "Russia": "RU",
        "Bahamas, The": "BS",
        "Byelarus": "BY",
        "Brunei": "BN",
        "Cape Verde": "CV",
        "China, Hong Kong Special Administrative Region": "HK",
        "Democratic Republic of the Congo": "CD",
        "Falkland Islands": "FK",
        "Gambia, The": "GM",
        "Ivory Coast": "CI",
        "Macedonia": "MK",
        "Myanmar (Burma)": "MM",
        "Netherlands Antilles": "AN",
        "Reunion": "RE",
        "Sao Tomo and Principe": "ST",
        "St. Vincent and the Grenadines": "VC",
        "Svalbard": "SJ",
        "Swaziland": "SZ",
        "US Virgin Islands": "VI",
        "Western Samoa": "WS",
    }
    try:
        return pyc.countries.lookup(name).alpha_2
    except LookupError:
        try:
            return extra_mappings[name]
        except LookupError:
            print("Country code not found for ", name)
            return None  # Return None if country not found


def dr_s(D_cba):
    print("Calculating dr_s")
    columns = {}
    for series_name, series in D_cba.items():
        series_sum = series.sum()
        columns[series_name] = series / series_sum
    dr_s = pd.DataFrame(columns)
    return dr_s

def dr_u(dr_s):
    print("Calculating dr_u")
    row_eu_countries = {
        'AL': 'Albania',
        'AZ': 'Azerbaijan',
        'BA': 'Bosnia and Herzegovina',
        'BY': 'Belarus',
        'IS': 'Iceland',
        'GL': 'Greenland',
        'GE': 'Georgia',
        'MK': 'Macedonia',
        'MD': 'Moldova',
        'RS': 'Serbia',
        'UA': 'Ukraine',
        # overseas territories of EU countries 
        'GP': 'Guadeloupe',
        'GF': 'French Guiana',
        'RE': 'Reunion',
        'VC': 'Saint Vincent and the Grenadines',
    }

    row_asia_pacific_countries = {
        'BD': 'Bangladesh', 'BN': 'Brunei', 'BT': 'Bhutan',
        'KH': 'Cambodia', 'FJ': 'Fiji',
        'KZ': 'Kazakhstan', 'KG': 'Kyrgyzstan', 'LA': 'Laos', 'MY': 'Malaysia', 'MV': 'Maldives',
        'MN': 'Mongolia', 'MM': 'Myanmar (Burma)', 'NP': 'Nepal', 'NZ': 'New Zealand',
        'KP': 'North Korea', 'PK': 'Pakistan', 'PG': 'Papua New Guinea', 'PH': 'Philippines',
        'WS': 'Samoa', 'SB': 'Solomon Islands', 'LK': 'Sri Lanka', 'SG': 'Singapore',
        'TJ': 'Tajikistan', 'TH': 'Thailand', 'TO': 'Tonga', 'TM': 'Turkmenistan',
        'UZ': 'Uzbekistan', 'VU': 'Vanuatu', 'VN': 'Vietnam'
    }

    row_african_countries = {
        'DZ': 'Algeria', 'AO': 'Angola', 'BJ': 'Benin', 'BW': 'Botswana', 'BF': 'Burkina Faso', 'BI': 'Burundi',
        'CM': 'Cameroon', 'CV': 'Cape Verde', 'CF': 'Central African Republic', 'TD': 'Chad', 'KM': 'Comoros',
        'CG': 'Congo', 'CD': 'Congo DRC', 'DJ': 'Djibouti', 'EG': 'Egypt', 'EH': 'Western Sahara', 'GQ': 'Equatorial Guinea', 'ER': 'Eritrea',
        'ET': 'Ethiopia', 'GA': 'Gabon', 'GM': 'Gambia, The', 'GH': 'Ghana', 'GN': 'Guinea', 'GW': 'Guinea-Bissau',
        'CI': 'Ivory Coast', 'KE': 'Kenya', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libya', 'MG': 'Madagascar',
        'MW': 'Malawi', 'ML': 'Mali', 'MR': 'Mauritania', 'MU': 'Mauritius', 'MA': 'Morocco', 'MZ': 'Mozambique', 'MQ': 'Martinique',
        'NA': 'Namibia', 'NE': 'Niger', 'NG': 'Nigeria', 'RW': 'Rwanda', 'ST': 'São Tomé and Príncipe', 'SN': 'Senegal',
        'SL': 'Sierra Leone', 'SO': 'Somalia', 'SZ': 'Eswatini',
        'SD': 'Sudan', 'TZ': 'Tanzania', 'TG': 'Togo', 'TN': 'Tunisia', 'UG': 'Uganda', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'
    }

    row_american_countries = {
        'AW': 'Aruba', 'AR': 'Argentina', 'BS': 'Bahamas, The', 'BZ': 'Belize', 'BO': 'Bolivia',
        'BB': 'Barbados', 'CL': 'Chile', 'CO': 'Colombia', 'CR': 'Costa Rica', 'CU': 'Cuba', 'DO': 'Dominican Republic',
        'EC': 'Ecuador', 'SV': 'El Salvador', 'GD': 'Grenada', 'GT': 'Guatemala', 'GY': 'Guyana', 'HT': 'Haiti', 'HN': 'Honduras', 'JM': 'Jamaica',
        'NI': 'Nicaragua', 'PA': 'Panama', 'PY': 'Paraguay', 'PE': 'Peru', 'PR': 'Puerto Rico', 'LC': 'Saint Lucia',
        'SR': 'Suriname', 'TT': 'Trinidad and Tobago', 'UY': 'Uruguay', 'VE': 'Venezuela'
    }

    row_middle_eastern_countries = {
        'AF': 'Afghanistan', 'AM': 'Armenia', 'BH': 'Bahrain',
        'IR': 'Iran', 'IQ': 'Iraq', 'IL': 'Israel', 'JO': 'Jordan', 'KW': 'Kuwait', 'LB': 'Lebanon', 'OM': 'Oman',
        'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SY': 'Syria', 'AE': 'United Arab Emirates',
        'YE': 'Yemen'
    }

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
    dr_u = dr_u.drop(index=row_regions.keys(), level='region')

    all_row_region_keys = list(row_eu_countries.keys()) + list(row_asia_pacific_countries.keys()) + list(row_african_countries.keys()) + list(row_american_countries.keys()) + list(row_middle_eastern_countries.keys())
    # build a mapping of country codes to region dataframes
    country_to_region = {}
    for region in all_row_region_keys:
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
            raise ValueError(f"Unknown region: {region}")

    # add all new regions to dr_u
    all_indices = []
    all_data = []
    for region in all_row_region_keys:
        region_data = country_to_region[region].copy()
        idx = pd.MultiIndex.from_product([[region],region_data.index], names=['region', 'sector'])
        all_indices.append(idx)
        all_data.append(region_data)

    combined_idx = pd.MultiIndex.from_tuples(
        [idx for subidx in all_indices for idx in subidx]
    )

    combined_data = pd.concat(all_data)
    combined_data.index = combined_idx

    dr_u = pd.concat([dr_u, combined_data])
    return dr_u


def dr_f(exio3_19, dr_u, stressor_name):
    print(f"Calculating dr_f for {stressor_name}")
    # use 2019 impact factors for calculating dr_f
    # calculate dr_f - share of the driver of biodiversity loss in impact region i from the total amount of the driver that is driven by consumption in consumption region j, product sector k
    dr_f = dr_u.copy()
    total = exio3_19.satellite.M.loc[stressor_name]
    scalars = total.to_numpy() # multipliers for each column

    # multiply each column of dr_u by the respective column value from exio3_19 impact factors
    dr_f = dr_f * scalars # same as dr_f * diag(scalars) but more efficient with numpy broadcasting
    return dr_f


def pdf(lci, dr_f, stressor_name):
    print(f"Calculating PDF/€ {stressor_name}")
    lci["Country_Code"] = lci["Country"].apply(get_country_code)
    lci = lci.dropna(subset=["Country_Code"])
    lci.set_index("Country_Code", inplace=True)
    # Ensure lci index is unique before reindexing
    lci = lci[~lci.index.duplicated(keep='first')]
    # sort rows on lci in same order as dr_f.index.sortlevel
    lci_reindexed = lci.reindex(dr_f.index.get_level_values(0).unique())

    # build array from the relevent lci stressor
    # every value should be repeated 200 times (number of sectors)
    cf = lci_reindexed[stressor_name].to_numpy()
    cf = np.repeat(cf, 200) # 1D array of length 200 * number of regions in lci
    # expand cf_all_effects to match the shape of dr_f
    cf = np.tile(cf, (dr_f.shape[1], 1)).T

    pdf = dr_f * cf
    pdf_total = pdf.sum()
    return pdf_total


def ozone_formation(lci_ozone, exio3_19, exio3_11):
    print("Calculating PDF/€ ozone formation")
    nmvoc_diag = exio3_11.satellite.diag_stressor(("NMVOC - combustion - air"))
    nox_diag = exio3_11.satellite.diag_stressor(("NOx - combustion - air"))

    D_cba_nmvoc = calculate_cba(exio3_11, nmvoc_diag, exio3_11.L)
    D_cba_nox = calculate_cba(exio3_11, nox_diag, exio3_11.L)

    dr_s_nmvoc = dr_s(D_cba_nmvoc)
    dr_s_nox = dr_s(D_cba_nox)

    dr_u_nmvoc = dr_u(dr_s_nmvoc)
    dr_u_nox = dr_u(dr_s_nox)

    dr_f_nmvoc = dr_f(exio3_19, dr_u_nmvoc, "NMVOC - combustion - air")
    dr_f_nox = dr_f(exio3_19, dr_u_nox, "NOx - combustion - air")

    ozone_nmvoc = pdf(lci_ozone, dr_f_nmvoc, "NMVOC")
    ozone_nox = pdf(lci_ozone, dr_f_nox, "NOx")

    return ozone_nmvoc, ozone_nox


def climate_change(lci_climate, exio3_19):
    print("Calculating PDF/€ ozone formation")

    # TODO: this grouping should be checked
    groups = exio3_19.satellite.get_index(as_dict=True, grouping_pattern={
        "CO2.*": "CO2 - Total",
        "CH4 - waste - air": "CH4",
        "CH4 - agriculture - air": "CH4",
        "CH4 - non combustion - Oil refinery - air": "CH4 fossil",
        "CH4 - non combustion - Mining of sub-bituminous coal - air": "CH4 fossil",
        "CH4 - non combustion - Mining of lignite (brown coal) - air": "CH4 fossil",
        "CH4 - non combustion - Mining of antracite - air": "CH4 fossil",
        "CH4 - non combustion - Mining of coking coal - air": "CH4 fossil",
        "CH4 - non combustion - Mining of bituminous coal - air": "CH4 fossil",
        "CH4 - non combustion - Extraction/production of (natural) gas - air": "CH4 fossil",
        "CH4 - non combustion - Extraction/production of crude oil": "CH4 fossil", 
        "CH4 - combustion - air": "CH4 fossil",
        "NOx.*": "NOx - Total",
        })

    satellite_agg = exio3_19.satellite.copy()

    for df_name, df in zip(satellite_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    satellite_agg.get_DataFrame(data=True, with_unit=True, with_population=False)):
        if df_name == "unit":
            satellite_agg.__dict__[df_name] = df.groupby(groups).apply(lambda x: " & ".join(x.unit.unique()))
        else:
            satellite_agg.__dict__[df_name] = df.groupby(groups).sum()


    # TODO: check if using 'all effects 100yrs' is correct
    # TODO: check if summing up all effects is correct
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
    
    return climate_aquatic, climate_terrestrial


def calculate_all(lci_path, exio_19_path, exio_11_path):
    lci_climate, lci_ozone, lci_acidification, lci_freshwater_eutrophication, lci_marine_eutrophication, lci_land, lci_water = load_lci(lci_path)

    # exiobase 2019 is used for impact factors
    exio3_19 = pymrio.parse_exiobase3(path=exio_19_path)
    # exiobase 2011 is used for calculating share of stressor for each region-product pair
    exio3_11 = pymrio.parse_exiobase3(path=exio_11_path)
    print("Calculating A (exio3_11)")
    exio3_11.A = pymrio.calc_A(exio3_11.Z, exio3_11.x)
    print("Calculating L (exio3_11)")
    exio3_11.L = pymrio.calc_L(exio3_11.A)

    # Calculate climate change impact
    climate_aquatic, climate_terrestrial = climate_change(lci_climate, exio3_19)

    # Calculate ozone formation impact
    ozone_nmvoc, ozone_nox = ozone_formation(lci_ozone, exio3_19, exio3_11)

    # Write the results
    pd.DataFrame(climate_aquatic).to_csv("pipeline/output/pdf-climate-aquatic.csv", index=True)
    pd.DataFrame(climate_terrestrial).to_csv("pipeline/output/pdf-climate-terrestrial.csv", index=True)
    pd.DataFrame(ozone_nmvoc).to_csv("pipeline/output/pdf-ozone-nmvoc.csv", index=True)
    pd.DataFrame(ozone_nox).to_csv("pipeline/output/pdf-ozone-nox.csv", index=True)


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

        calculate_all(data['lc_impact_path'], data['exio_19_path'], data['exio_11_path'])
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON file. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()