import xarray as xr
from pandas import to_datetime, date_range, DateOffset
import numpy as np
import os


def compress_netcfd(folder_path, out_folder, file_name):
    """
    Takes the 52 individual ensembles and combines them into one compact NetCDF file, saving disk space in the process
    by eliminating the forecasts that aren't daily.

    Parameters
    ----------

    folder_path: str
        The path to the folder containing the 52 ensemble forecast files in NetCDF format

    out_folder: str
        The path to the folder that you want the more compact NetCDF file in.

    file_name: str
        The name of the region. For example, if the files followed the pattern of "Qout_africa_continental_1.nc,
        this argument would be "Qout_africa_continental"
    """

    # Based on 15 day forecast
    forecast_day_indices = np.array([0, 8, 16, 24, 32, 40, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84], dtype=np.int8)

    # Based on 10 day forecast
    # Excluding the first day because we already have initialization from the normal forecasts
    high_res_forecast_day_indices = np.array([24, 48, 72, 92, 100, 108, 112, 116, 120, 124])

    # Getting the number of rivids and start date
    tmp_file = os.path.join(folder_path, "{}_{}.nc".format(file_name, 1))
    tmp_dataset = xr.open_dataset(tmp_file)

    start_datetime = to_datetime(tmp_dataset["time"].values[0])
    num_of_rivids = tmp_dataset['rivid'].size

    tmp_dataset.close()

    dates = date_range(start_datetime + DateOffset(1), periods=15)
    high_res_dates = date_range(start_datetime + DateOffset(1), periods=10)

    # Ensemble Dimensions
    #  1) Rivid
    #  2) Number of forecast days (i.e. 15 in a 15 day forecast)
    #  3) Number of ensembles
    ensembles = np.zeros((num_of_rivids, 15, 51), dtype=np.float32)
    initialization = np.zeros((num_of_rivids,), dtype=np.float32)

    for forecast_number in range(1, 52):
        file = os.path.join(folder_path, "{}_{}.nc".format(file_name, forecast_number))

        tmp_dataset = xr.open_dataset(file)
        streamflow = tmp_dataset['Qout'].data
        streamflow = streamflow[:, forecast_day_indices]

        if forecast_number == 1:
            initialization[:] = streamflow[:, 0]
            rivids = tmp_dataset['rivid'].data
            lat = tmp_dataset['lat'].data
            lon = tmp_dataset['lon'].data
            z = tmp_dataset['z'].data

        ensembles[:, :, forecast_number - 1] = streamflow[:, 1:]

        tmp_dataset.close()

    # High Res Forecast
    file = os.path.join(folder_path, "{}_52.nc".format(file_name))

    tmp_dataset = xr.open_dataset(file)

    high_res_forecast_data = tmp_dataset["Qout"].data
    high_res_forecast_data = high_res_forecast_data[:, high_res_forecast_day_indices]

    tmp_dataset.close()

    data_variables = {
        "Qout": (['rivid', 'date', 'ensemble_number'], ensembles),
        "Qout_high_res": (['rivid', 'date_high_res'], high_res_forecast_data)
    }

    coords = {
        'rivid': rivids,
        'date': dates,
        'date_high_res': high_res_dates,
        'ensemble_number': np.arange(1, 52, dtype=np.uint8),
        'initialization_values': ('rivid', initialization),
        'lat': ('rivid', lat),
        'lon': ('rivid', lon),
        'z': ('rivid', z),
        'start_date': start_datetime
    }

    xarray_dataset = xr.Dataset(data_variables, coords)
    start_date_string = start_datetime.strftime("%Y%m%d")
    xarray_dataset.to_netcdf(path=os.path.join(out_folder, '{}.nc'.format(start_date_string)), format='NETCDF4')


if __name__ == "__main__":
    pass
