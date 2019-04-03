import os
import pandas as pd
import numpy as np


def organize_api_forecasts(forecast_dir_path, out_dir_path, daily=True):
    """
    Organize the contents of a folder with forecasts that have been stored in CSV format from the Streamflow Prediction
    tool REST API. This will create seperate CSVs that contain the 1-Day, 2-Day... forecasts from the given CSV files.

    Parameters
    ----------

    forecast_dir_path: str
        The path to the directory that contains all of the forecast files in CSV format that have been downloaded from
        the Streamflow Prediction Tool REST API. Note, the files will be sorted, so choose a naming convention that
        will be sorted properly (YYYYMMDD format works nicely, but whatever you choose that will be sorted in the
        correct order works.

    out_dir_path: str
        The path to the directory where the resulting organized files will be dumped.

    daily: bool
        If True (default), only daily values will be saved (i.e. one day forecasts). If not, then all of the time
        frequencies will be used (i.e. three hour forecasts, 6 hour forecasts, etc). Note that setting this parameter to
        false will generate many files.

    """

    # Get all of the sorted files
    files = sorted([os.path.join(forecast_dir_path, i) for i in os.listdir(forecast_dir_path)])
    num_start_dates = len(files)

    # Initialize NumPy arrays to store the data in the files
    if daily:
        all_forecast_array = np.zeros((15, 51, num_start_dates))
        all_high_res_forecast_array = np.zeros((10, num_start_dates))
        initialization_array = np.zeros((num_start_dates, ))
    else:
        all_forecast_array = np.zeros((84, 51, num_start_dates))
        all_high_res_forecast_array = np.zeros((124, num_start_dates))
        initialization_array = np.zeros((num_start_dates,))

    initial_dates_list = []
    for i, file in enumerate(files):

        file_df = pd.read_csv(file, index_col=0)
        file_df.index = pd.to_datetime(file_df.index)

        initial_dates_list.append(file_df.index[0])
        initial_value = file_df.iloc[0, 0]  # Initialization value of forecast

        if daily:

            if i == 0:
                # Creating a list of (Day, Hour) tuples (Assumes 15 day forecasts and 10 days of high resolution)
                forecasts_day_hour_list = [(i + 1, 0) for i in range(15)]
                high_res_forecast_day_hour_list = [(i + 1, 0) for i in range(10)]

            forecasts_df = file_df.iloc[:, :-1].dropna()
            forecast_daily_indices = np.where(forecasts_df.index.hour == 0)[0][1:]  # Remove initial value
            forecasts_array = forecasts_df.iloc[forecast_daily_indices, :].values

            high_res_forecast_series = file_df.iloc[:, -1].dropna()
            high_res_forecast_daily_indices = np.where(high_res_forecast_series.index.hour == 0)[0][1:]
            high_res_forecast_array = high_res_forecast_series.iloc[high_res_forecast_daily_indices].values

            all_forecast_array[:, :, i] = forecasts_array
            all_high_res_forecast_array[:, i] = high_res_forecast_array
            initialization_array[i] = initial_value

        else:
            # Getting daily forecast values
            forecasts_df = file_df.iloc[:, :-1].dropna()
            forecasts_array = forecasts_df.values[1:, :]

            high_res_forecast_series = file_df.iloc[:, -1].dropna()
            high_res_forecast_array = high_res_forecast_series.values[1:]

            all_forecast_array[:, :, i] = forecasts_array
            all_high_res_forecast_array[:, i] = high_res_forecast_array
            initialization_array[i] = initial_value

            if i == 0:
                # Creating a list of (Day, Hour) tuples
                forecasts_day_hour_list = []
                for date in forecasts_df.index[1:]:

                    timedelta_object = date - forecasts_df.index[0]
                    timedelta_components = list(timedelta_object.components)

                    day_hour_tuple = (timedelta_components[0], timedelta_components[1])
                    forecasts_day_hour_list.append(day_hour_tuple)

                high_res_forecast_day_hour_list = []
                for date in high_res_forecast_series.index[1:]:

                    timedelta_object = date - forecasts_df.index[0]
                    timedelta_components = timedelta_object.components

                    day_hour_tuple = (timedelta_components[0], timedelta_components[1])
                    high_res_forecast_day_hour_list.append(day_hour_tuple)

    for i, (day, hour) in enumerate(forecasts_day_hour_list):
        data = all_forecast_array[i, :, :].T

        forecasts_out_file_name = "{}_Day_{}_Hour_Forecast.csv".format(day, hour)
        # time_series = pd.date_range(  # TODO: Try to make this so it could accept forecasts if not consistent frequency
        #     start=initial_date + pd.DateOffset(days=day, hours=hour), freq="1D", periods=num_start_dates
        # )

        # Write data to CSV
        forecast_out_file_path = os.path.join(out_dir_path, forecasts_out_file_name)
        out_df = pd.DataFrame(
            data, index=initial_dates_list, columns=["Ensemble_{} (m^3/s)".format(i) for i in range(data.shape[1])]
        )
        out_df.index += pd.DateOffset(days=day, hours=hour)
        out_df.to_csv(forecast_out_file_path, index_label="Datetime")


    # high_res_forecast_out_file_name = ""



if __name__ == "__main__":

    organize_api_forecasts(r"/home/wade/Documents/Saved_Forecasts/", r"/home/wade/Documents/Organized_Forecasts/", daily=True)
