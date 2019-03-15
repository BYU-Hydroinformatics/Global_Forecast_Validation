import xarray as xr
import pandas as pd
import numpy as np
import os
import numba as nb
import time
import dask.array as da
from progress.bar import FillingCirclesBar


def compute_all(work_dir, out_path, memory_to_allocate_gb, starting_date=None, ending_date=None):
    """
    Computes forecast metrics for all of the streams in a region. Note that this function assumes that the same naming
    convention as the `compress_netcdf.py` file produces is used (i.e. YYYYMMDD.nc as the file names).

    Parameters
    ----------

    work_dir: str
        The directory that contains all of the forecast files that were created with the compress_netcdf function. Make
        sure that this directory only contains the compressed forecast files.

    out_path: str
        The path where the resulting CSV of results should be stored. Include the file name in this path! For example,
        if I wanted the file to be stored in the same directory as I ran the script in, I would simply set this
        parameter to be the name of the file (ie Skill_Scores.csv).

    memory_to_allocate_gb: float
        Indicates the memory that you would like to be allocated on the computer when running the program. It is highly
        recommended to be conservative in this number as slightly more memory may be consumed (maybe up to half a gig
        in very large regions).

    starting_date: str
        The starting date of the analysis formatted as YYYY-MM-DD (i.e. January 2, 2019 would be 2019-01-02).

    ending_date: str
        The ending date of the analysis formatted as YYYY-MM-DD (i.e. January 2, 2019 would be 2019-01-02).

    """
    # Checking how many rivids can be held in memory
    array_size_bytes = 3060  # Based on 15 x 51 member array
    memory_to_allocate_bytes = memory_to_allocate_gb * 1e9

    # Getting the file names
    if (starting_date is None) and (ending_date is None):
        files = [os.path.join(work_dir, i) for i in os.listdir(work_dir)]
        files.sort()
    elif starting_date and ending_date:
        dates_range = pd.date_range(starting_date, ending_date)
        date_strings = dates_range.strftime("%Y%m%d").tolist()
        files = [os.path.join(work_dir, i + ".nc") for i in date_strings]
    else:
        raise RuntimeError("Either both the starting and ending date must be specified or neither.")

    # Calculating the size of the chunk of data that can be held in memory
    chunk_size = int(np.floor(memory_to_allocate_bytes / ((array_size_bytes * len(files)) + len(files))))

    # Creating a large dask array with all of the data in it
    list_of_dask_q_arrays = []
    list_of_dask_init_arrays = []

    for file in files:
        ds = xr.open_dataset(file, chunks={"rivid": chunk_size})

        tmp_dask_q_array = ds["Qout"].data
        list_of_dask_q_arrays.append(tmp_dask_q_array)

        tmp_dask_init_array = ds["initialization_values"].data
        list_of_dask_init_arrays.append(tmp_dask_init_array)

        ds.close()

    big_dask_q_array = da.stack(list_of_dask_q_arrays)
    big_dask_init_array = da.stack(list_of_dask_init_arrays)

    # Retrieving the number of streams and their corresponding Rivids
    tmp_dataset = xr.open_dataset(files[0])

    num_of_streams = tmp_dataset['rivid'].size
    rivids = tmp_dataset['rivid'].data

    tmp_dataset.close()

    # Calculating the amount of iterations necessary to loop through all of the rivid chunks
    num_chunk_iterations = int(np.ceil(num_of_streams / chunk_size))
    start_chunk = 0
    end_chunk = chunk_size
    list_of_tuples_with_metrics = []

    # Main Loop
    filling = FillingCirclesBar('Validating Forecasts', max=num_chunk_iterations)  # Progress bar
    for chunk_number in range(num_chunk_iterations):

        big_forecast_data_array = np.asarray(big_dask_q_array[:, start_chunk:end_chunk, :, :])
        big_init_data_array = np.asarray(big_dask_init_array[:, start_chunk:end_chunk])

        rivids_chunk = rivids[start_chunk:end_chunk]

        # Main calculations, performed with Numba and the LLVM compiler infrastructure
        results_array = numba_calculate_metrics(
            big_forecast_data_array, big_init_data_array, len(files), big_forecast_data_array.shape[1], 15, rivids_chunk
        )

        for rivid in range(results_array.shape[1]):
            for forecast_day in range(results_array.shape[0]):
                tmp_array = results_array[forecast_day, rivid, :]
                tuple_to_append = (
                    rivids_chunk[rivid], forecast_day + 1, tmp_array[0], tmp_array[1], tmp_array[2], tmp_array[3],
                    tmp_array[4], tmp_array[5], tmp_array[6], tmp_array[7], tmp_array[8], tmp_array[9], tmp_array[10],
                    tmp_array[11], tmp_array[12], tmp_array[13], tmp_array[14]
                )
                list_of_tuples_with_metrics.append(tuple_to_append)

        start_chunk += chunk_size
        end_chunk += chunk_size

        filling.next()  # Next progress bar

    filling.finish()

    print("Writing results to file")
    # Creating a dataframe with the results of the analysis
    final_df = pd.DataFrame(
        list_of_tuples_with_metrics,
        columns=[
            'Rivid', 'Forecast Day', 'CRPS', 'CRPS BENCH', 'CRPSS', "MAE", "MAE_BENCH", "MAESS", "MSE", "MSE_BENCH",
            "MSESS", "RMSE", "RMSE_BENCH", "RMSESS", "Pearson_r", "Pearson_r_BENCH", "Pearson_r_SS"
        ])

    final_df.to_csv(out_path, index=False)
    print("Finished")


@nb.njit(parallel=True)
def numba_calculate_metrics(forecast_array, initialization_array, number_of_start_dates, number_of_streams,
                            num_forecast_days, rivid_array):
    """
    Parameters
    ----------

    forecast_array: 4D ndarray
        A 4 dimensional numPy array with the following dimensions: 1) Start Date Number (365 if there are a year's
        forecasts), 2) Unique stream ID, 3) Forecast Days (e.g. 1-15 in a 15 day forecast), 4) Ensembles

    initialization_array: 2D ndarray
        A 2 dimenensional NumPy array with the following dimensions: 1) Start Dates, 2) Unique stream ID

    number_of_start_dates: The number of start dates for the analysis to perform

    number_of_streams:
        The number of streams in the analysis

    num_forecast_days:
        The number of forecast days in the analysis

    rivid_array:
        A 1d array containing the rivids for the streams to be analyzed

    Returns
    -------
    ndarray
        An ndarray with the following dimensions:

        1) Forecast Day: 1-15 in the case of a 15 day forecast
        2) Rivid: The stream unique ID
        3) Metrics: CRPS, CRPS_BENCH, CRPSS, MAE, MAE_BENCH, MAESS, MSE, MSE_BENCH, MSESS, RMSE, RMSE_BENCH, RMSESS,
                    Pearson_r, Pearson_r_BENCH, Pearson_r_SS

    """

    return_array = np.ones((num_forecast_days, number_of_streams, 15), dtype=np.float32)

    for stream in nb.prange(number_of_streams):
        for forecast_day in range(num_forecast_days):
            initialization_vals = initialization_array[(forecast_day + 1):, stream]
            forecasts = forecast_array[:(number_of_start_dates - (forecast_day + 1)), stream, forecast_day, :]
            benchmark_forecasts = initialization_array[:(number_of_start_dates - (forecast_day + 1)), stream]

            # Calculating the CRPSS
            crps = ens_crps(initialization_vals, forecasts)
            crps_bench = mae(initialization_vals, benchmark_forecasts)
            if crps_bench == 0:
                crpss = np.inf
                print("Warning: Division by zero on: ", rivid_array[stream])
            else:
                crpss = 1 - crps / crps_bench

            # Calculating MAE_SS
            mae_val = ens_mae(initialization_vals, forecasts)
            if crps_bench == 0:
                maess = np.inf
            else:
                maess = 1 - mae_val / crps_bench

            # Calculating the MSE_SS
            mse_val = ens_mse(initialization_vals, forecasts)
            mse_bench = mse(initialization_vals, benchmark_forecasts)
            if mse_bench == 0:
                msess = np.inf
            else:
                msess = 1 - mse_val / mse_bench

            # Calculating the RMSE_SS
            rmse_val = ens_rmse(initialization_vals, forecasts)
            rmse_bench = rmse(initialization_vals, benchmark_forecasts)
            if rmse_bench == 0:
                rmsess = np.inf
            else:
                rmsess = 1 - rmse_val / rmse_bench

            # Calculating the Pearson_r_SS
            pearson_r_val = ens_pearson_r(initialization_vals, forecasts)
            pearson_r_bench = pearson_r(initialization_vals, benchmark_forecasts)
            if pearson_r_bench == 0:
                pearson_r_ss = np.inf
            else:
                pearson_r_ss = pearson_r_ss = 1 - (pearson_r_val - 1) / (pearson_r_bench - 1)

            # Adding metrics to the return array
            return_array[forecast_day, stream, 0] = crps
            return_array[forecast_day, stream, 1] = crps_bench
            return_array[forecast_day, stream, 2] = crpss
            return_array[forecast_day, stream, 3] = mae_val
            return_array[forecast_day, stream, 4] = crps_bench  # Same as the mae_bench
            return_array[forecast_day, stream, 5] = maess
            return_array[forecast_day, stream, 6] = mse_val
            return_array[forecast_day, stream, 7] = mse_bench
            return_array[forecast_day, stream, 8] = msess
            return_array[forecast_day, stream, 9] = rmse_val
            return_array[forecast_day, stream, 10] = rmse_bench
            return_array[forecast_day, stream, 11] = rmsess
            return_array[forecast_day, stream, 12] = pearson_r_val
            return_array[forecast_day, stream, 13] = pearson_r_bench
            return_array[forecast_day, stream, 14] = pearson_r_ss

    return return_array


@nb.njit()
def ens_crps(obs, fcst_ens, adj=np.nan):

    rows = obs.size
    cols = fcst_ens.shape[1]

    col_len_array = np.ones(rows) * cols
    sad_ens_half = np.zeros(rows)
    sad_obs = np.zeros(rows)
    crps = np.zeros(rows)

    crps = numba_crps(
        fcst_ens, obs, rows, cols, col_len_array, sad_ens_half, sad_obs, crps, np.float64(adj)
    )

    # Calc mean crps as simple mean across crps[i]
    crps_mean = np.mean(crps)

    return crps_mean


@nb.njit()
def numba_crps(ens, obs, rows, cols, col_len_array, sad_ens_half, sad_obs, crps, adj):
    for i in range(rows):
        the_obs = obs[i]
        the_ens = ens[i, :]
        the_ens = np.sort(the_ens)
        sum_xj = 0.
        sum_jxj = 0.

        j = 0
        while j < cols:
            sad_obs[i] += np.abs(the_ens[j] - the_obs)
            sum_xj += the_ens[j]
            sum_jxj += (j + 1) * the_ens[j]
            j += 1

        sad_ens_half[i] = 2.0 * sum_jxj - (col_len_array[i] + 1) * sum_xj

    if np.isnan(adj):
        for i in range(rows):
            crps[i] = sad_obs[i] / col_len_array[i] - sad_ens_half[i] / \
                      (col_len_array[i] * col_len_array[i])
    elif adj > 1:
        for i in range(rows):
            crps[i] = sad_obs[i] / col_len_array[i] - sad_ens_half[i] / \
                      (col_len_array[i] * (col_len_array[i] - 1)) * (1 - 1 / adj)
    elif adj == 1:
        for i in range(rows):
            crps[i] = sad_obs[i] / col_len_array[i]
    else:
        for i in range(rows):
            crps[i] = np.nan

    return crps


@nb.njit()
def mean_axis_1(forecasts):
    nrows = forecasts.shape[0]
    ncols = forecasts.shape[1]

    return_vector = np.empty((nrows,))

    for i in range(nrows):
        mean_tmp = 0

        for j in range(ncols):
            mean_tmp += forecasts[i, j]

        mean_tmp /= ncols
        return_vector[i] = mean_tmp

    return return_vector


@nb.njit()
def mae(obs, sim):
    return np.mean(np.abs(sim - obs))


@nb.njit()
def ens_mae(obs, forecasts):

    fcst_ens_mean = mean_axis_1(forecasts)
    error = fcst_ens_mean - obs

    return np.mean(np.abs(error))


@nb.njit()
def mse(obs, sim):
    return np.mean(((sim - obs)**2))


@nb.njit()
def ens_mse(obs, forecasts):

    fcst_ens_mean = mean_axis_1(forecasts)
    error = fcst_ens_mean - obs

    return np.mean(error ** 2)


@nb.njit()
def rmse(obs, sim):

    return np.sqrt(np.mean((sim - obs)**2))


@nb.njit()
def ens_rmse(obs, forecasts):

    fcst_ens_mean = mean_axis_1(forecasts)
    error = fcst_ens_mean - obs

    return np.sqrt(np.mean(error ** 2))


@nb.njit()
def pearson_r(obs, sim):
    sim_mean = np.mean(sim)
    obs_mean = np.mean(obs)

    top = np.sum((obs - obs_mean) * (sim - sim_mean))
    bot1 = np.sqrt(np.sum((obs - obs_mean) ** 2))
    bot2 = np.sqrt(np.sum((sim - sim_mean) ** 2))

    if (bot1 * bot2) != 0:
        return top / (bot1 * bot2)
    else:
        return np.nan


@nb.njit()
def ens_pearson_r(obs, forecasts):

    fcst_ens_mean = mean_axis_1(forecasts)

    sim_mean = np.mean(fcst_ens_mean)
    obs_mean = np.mean(obs)

    top = np.sum((obs - obs_mean) * (fcst_ens_mean - sim_mean))
    bot1 = np.sqrt(np.sum((obs - obs_mean) ** 2))
    bot2 = np.sqrt(np.sum((fcst_ens_mean - sim_mean) ** 2))

    if (bot1 * bot2) != 0:
        return top / (bot1 * bot2)
    else:
        return np.nan


if __name__ == "__main__":

    start = "2017-06-01"
    end = "2017-10-31"

    dates_range = pd.date_range(start, end)
    dates_strings = dates_range.strftime("%Y%m%d").tolist()

    workspace = r'/Users/wade/Documents/South_Asia2017'
    output_file = r'/Users/wade/PycharmProjects/Forecast_Validation/South_Asia.csv'
    MEMORY_TO_ALLOCATE = 1.0  # GB

    start = time.time()
    compute_all(workspace, output_file, MEMORY_TO_ALLOCATE)
    end = time.time()
    print(end - start)
