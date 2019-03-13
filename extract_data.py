import xarray as xr
import dask.array as da
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
    ensemble_columns = ["Ensemble_{}".format(i) for i in range(51)]

    # Generate start date time series
    dates_list = sorted([i[:-3] for i in os.listdir(folder_path)])
    dates_pandas = pd.to_datetime(dates_list)

    # Get rivids as an array
    ds = xr.open_dataset(files[0])
    rivids = ds["rivid"].data
    ds.close()

    # Try to find the index of the rivid
    try:
        rivid_index = np.where(rivids == rivid)[0][0]
    except Exception as e:
        raise ValueError("The given rivid does not exist in this stream network.")

    # Creating dask dataframes for the data
    list_of_dask_q_arrays = []
    list_of_dask_init_arrays = []
    list_of_dask_q_high_res_arrays = []

    for file in files:
        ds = xr.open_dataset(file, chunks={"rivid": 5000})  # arbitrary chunk value

        tmp_dask_q_array = ds["Qout"].data
        list_of_dask_q_arrays.append(tmp_dask_q_array)

        tmp_dask_init_array = ds["initialization_values"].data
        list_of_dask_init_arrays.append(tmp_dask_init_array)

        tmp_dask_q_high_res_array = ds["Qout_high_res"].data
        list_of_dask_q_high_res_arrays.append(tmp_dask_q_high_res_array)

        ds.close()

    big_dask_q_array = da.stack(list_of_dask_q_arrays)
    big_dask_init_array = da.stack(list_of_dask_init_arrays)
    big_dask_q_high_res_array = da.stack(list_of_dask_q_high_res_arrays)

    # Extracting the initialization flows
    init_data = np.asarray(big_dask_init_array[:, rivid_index])
    init_df = pd.DataFrame(init_data, columns=["Initialization (m^3/s)"], index=dates_pandas)
    file_name = os.path.join(outpath, "Initialization_Values.csv")
    init_df.to_csv(file_name, index_label="Date")

    # Extracting the Flow Data
    q_data = np.asarray(big_dask_q_array[:, rivid_index, :, :])
    for i in range(15):

        q_data_tmp = q_data[:, i, :]

        temp_df = pd.DataFrame(
            q_data_tmp, index=(dates_pandas + pd.DateOffset(days=(i + 1))), columns=ensemble_columns
        )

        file_name = "{}_Day_Forecasts.csv".format(i + 1)
        temp_df.to_csv(os.path.join(outpath, file_name), index_label="Date")

    # Extracting the high resolution flow data
    q_high_res_data = np.asarray(big_dask_q_high_res_array[:, rivid_index, :])
    for i in range(10):

        q_high_res_data_tmp = q_high_res_data[:, i]

        temp_df = pd.DataFrame(
            q_high_res_data_tmp, index=(dates_pandas + pd.DateOffset(days=(i + 1))),
            columns=["High Resolution Forecast (m^3/s)"]
        )

        file_name = "{}_Day_Forecasts_High_Res.csv".format(i + 1)
        temp_df.to_csv(os.path.join(outpath, file_name), index_label="Date")


if __name__ == "__main__":
    path_to_files = r'/Users/wade/Documents/South_Asia2017'
    output_path = "/Users/wade/Downloads/62028_Files"

    extract_by_rivid(62028, path_to_files, output_path)

