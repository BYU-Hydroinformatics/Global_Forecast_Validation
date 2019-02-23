import xarray as xr
import pandas as pd
import numpy as np
import os


def extract_by_rivid(rivid, folder_path, outpath):
    """
    Extracts data from a folder with NetCDF forecast files (generated with the compress_netcdf function) into CSV files
    in the given path

    Parameters
    ----------

    rivid: int
        The rivid (COMID) of the desired stream to extract data for.

    folder_path: str
        The path to the folder containing the forecast NetCDF files.

    outpath: str
        The path to the directory that you would like to write the CSV files to.
    """

    files = sorted([os.path.join(folder_path, i) for i in os.listdir(folder_path)])
    num_start_dates = len(files)
    ensemble_columns = ["Ensemble_{}".format(i) for i in range(51)]

    # Get the index for the selected rivid
    ds = xr.open_dataset(files[0])

    rivids = ds["rivid"].data
    rivid_index = np.where(rivids == rivid)[0][0]

    ds.close()

    print(rivid_index)

    init_df = pd.DataFrame()
    # Extracting the Initialization values for each day
    for file in files:
        ds = xr.open_dataset(file)
        init_value = ds["initialization_values"].data[rivid_index]
        date = pd.to_datetime(ds["start_date"].data)

        init_df = init_df.append(pd.DataFrame(init_value, index=[date], columns=["Initialization (m^3/s)"]))

        ds.close()

    # Writing the init df to csv
    init_df.to_csv(os.path.join(outpath, "Initialization_Values.csv"), index_label="Date")

    # # Creating forecast files for each forecast day
    for i in range(15):

        data_array = np.zeros((num_start_dates, 51))
        dates = []

        for start_date, file in enumerate(files):
            ds = xr.open_dataset(file)
            forecasts = ds["Qout"].data[rivid_index, i, :]
            date = pd.to_datetime(ds["date"].data[i])

            data_array[start_date, :] = forecasts
            dates.append(date)
            # temp_df = temp_df.append(pd.DataFrame(forecasts.reshape(1, -1), index=[date], columns=ensemble_columns))

            ds.close()

        temp_df = pd.DataFrame(data_array, index=dates, columns=ensemble_columns)

        file_name = "{}_Day_Forecasts".format(i + 1)
        temp_df.to_csv(os.path.join(outpath, file_name), index_label="Date")

    # Creating forecast files for each forecast day
    for i in range(10):

        high_res_df = pd.DataFrame()
        # Extracting the Initialization values for each day
        for file in files:
            ds = xr.open_dataset(file)
            high_res_forecast = ds["Qout_high_res"].data[rivid_index, i]
            date = pd.to_datetime(ds["date_high_res"].data[i])

            high_res_df = high_res_df.append(pd.DataFrame(high_res_forecast, index=[date],
                                                          columns=["High Resolution Forecast (m^3/s)"]))

            ds.close()

        file_name = "{}_Day_Forecasts_High_Res".format(i + 1)
        high_res_df.to_csv(os.path.join(outpath, file_name), index_label="Date")


if __name__ == "__main__":
    path_to_files = r"/home/wade/Documents/South_Asia_Forecasts"
    output_path = "/home/wade/Downloads/Forecasts_CSV"

    extract_by_rivid(62712, path_to_files, output_path)
