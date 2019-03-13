import numpy as np
import pandas as pd
import unittest
from compress_netcdf import compress_netcfd
import os
import xarray as xr
from validate_forecasts import compute_all


class TestCompressNetcdf(unittest.TestCase):
    """
    Tests the functions included in compress_netcdf.py to make sure that they are working correctly with
    your python version.
    """

    def setUp(self):
        pass

    def test_compress_netcdf(self):
        start_date = "20190104"
        folder_path = 'Test_files/Individual_Ensembles'
        out_path = 'Test_files'
        compress_netcfd(folder_path, start_date, out_path, "Qout_south_america_continental", 10)

        ds = xr.open_dataset(os.path.join(os.getcwd(), out_path, start_date + ".nc"))

        flow_array = ds["Qout"].data
        flow_array_high_res = ds["Qout_high_res"].data
        initialization_values = ds["initialization_values"].data
        date = ds["date"].data
        date_high_res = ds["date_high_res"].data
        rivids = ds["rivid"].data

        benchmark_flow_array = np.load("Test_files/Comparison_Files/benchmark_flow_array.npy")
        benchmark_array_high_res = np.load("Test_files/Comparison_Files/benchmark_array_high_res.npy")
        benchmark_initialization_values = np.array([1.9156765937805176, 1.7540310621261597, 1.5276174545288086,
                                                    2.0937132835388184, 3.4932050704956055, 3.678524971008301,
                                                    0.854943037033081, 1.688418984413147, 13.452759742736816,
                                                    3.7613487243652344], dtype=np.float32)
        benchmark_date = np.array(['2019-01-05', '2019-01-06', '2019-01-07', '2019-01-08',
                                   '2019-01-09', '2019-01-10', '2019-01-11', '2019-01-12',
                                   '2019-01-13', '2019-01-14', '2019-01-15', '2019-01-16',
                                   '2019-01-17', '2019-01-18', '2019-01-19'],
                                  dtype='datetime64[ns]')
        benchmark_date_high_res = np.array(['2019-01-05', '2019-01-06', '2019-01-07', '2019-01-08',
                                            '2019-01-09', '2019-01-10', '2019-01-11', '2019-01-12',
                                            '2019-01-13', '2019-01-14'], dtype='datetime64[ns]')
        benchmark_rivids = np.array([192474, 192473, 192470, 192469, 192454, 192452, 192448, 192446, 192451, 192450],
                                    dtype=np.int32)

        print("Testing")
        self.assertTrue(np.all(np.isclose(flow_array, benchmark_flow_array)))
        self.assertTrue(np.all(np.isclose(flow_array_high_res, benchmark_array_high_res)))
        self.assertTrue(np.all(np.isclose(initialization_values, benchmark_initialization_values)))
        self.assertTrue(np.all(date == benchmark_date))
        self.assertTrue(np.all(date_high_res == benchmark_date_high_res))
        self.assertTrue(np.all(rivids == benchmark_rivids))

        ds.close()

    def tearDown(self):
        os.remove("Test_files/20190104.nc")


class TestValidateForecasts(unittest.TestCase):

    def setUp(self):
        work_dir = "Test_files/Forecast_Validation_Files"
        compute_all(work_dir, out_path="Test_files/Forecast_analysis_test.csv", memory_to_allocate_gb=1.0)

    def test_compress_netcdf(self):

        # # Code that can be used to generate the true values
        # import hydrostats.ens_metrics as em
        # import hydrostats.metrics as hm
        #
        # work_dir = "Test_files/Forecast_Validation_Files"
        # starting_date = "2018-08-19"
        # ending_date = "2018-12-16"
        #
        # dates_range = pd.date_range(starting_date, ending_date)
        # date_strings = dates_range.strftime("%Y%m%d").tolist()
        #
        # files = [os.path.join(work_dir, i + ".nc") for i in date_strings]
        #
        # data_sets = [xr.open_dataset(file) for file in files]
        #
        # true_data = []
        #
        # # Getting rivids
        # tmp_dataset = xr.open_dataset(files[0])
        #
        # rivids = tmp_dataset['rivid'].data.tolist()
        #
        # tmp_dataset.close()
        #
        # for i, rivid in enumerate(rivids):
        #     for forecast_day in range(15):
        #         dates = []
        #         init_dates = []
        #         data = []
        #         init_data = []
        #
        #         for ds in data_sets:
        #             dates.append(ds["date"].data[forecast_day])
        #             data.append(ds["Qout"].data[i, forecast_day, :])
        #
        #             init_data.append(ds["initialization_values"].data[i])
        #             init_dates.append(ds["start_date"].data)
        #
        #         pd_dates = pd.to_datetime(dates)
        #         np_data = np.array(data)
        #
        #         df = pd.DataFrame(np_data, index=pd_dates,
        #                           columns=["Ensemble {}".format(str(i).zfill(2)) for i in range(51)])
        #
        #         init_df = pd.DataFrame(init_data, index=pd.to_datetime(init_dates), columns=["Water Balance"])
        #
        #         benchmark_df = init_df.copy()
        #         benchmark_df.index = init_df.index + pd.DateOffset(forecast_day + 1)
        #         benchmark_df.columns = ["Benchmark"]
        #
        #         big_df = pd.DataFrame.join(init_df, [benchmark_df, df]).dropna()
        #
        #         obs = big_df.iloc[:, 0].values.astype(np.float64)
        #         benchmark = big_df.iloc[:, 1].values
        #         forecasts = big_df.iloc[:, 2:].values.astype(np.float64)
        #
        #         # CRPS
        #         crps = em.ens_crps(obs, forecasts)["crpsMean"]
        #         crps_bench = hm.mae(obs, benchmark)
        #         crpss = em.skill_score(crps, crps_bench, perf_score=0)["skillScore"]
        #
        #         # MAE
        #         mae = em.ens_mae(obs, forecasts)
        #         mae_bench = hm.mae(obs, benchmark)
        #         maess = em.skill_score(mae, mae_bench, perf_score=0)["skillScore"]
        #
        #         # MSE
        #         mse = em.ens_mse(obs, forecasts)
        #         mse_bench = hm.mse(obs, benchmark)
        #         msess = em.skill_score(mse, mse_bench, perf_score=0)["skillScore"]
        #
        #         # RMSE
        #         rmse = em.ens_rmse(obs, forecasts)
        #         rmse_bench = hm.rmse(obs, benchmark)
        #         rmsess = em.skill_score(rmse, rmse_bench, perf_score=0)["skillScore"]
        #
        #         # Pearson r
        #         pearson_r = em.ens_pearson_r(obs, forecasts)
        #         pearson_r_bench = hm.pearson_r(obs, benchmark)
        #         pearson_r_ss = em.skill_score(pearson_r, pearson_r_bench, perf_score=1)["skillScore"]
        #
        #         true_data.append(
        #             (rivid, forecast_day + 1, crps, crps_bench, crpss, mae, mae_bench, maess, mse, mse_bench,
        #              msess, rmse, rmse_bench, rmsess, pearson_r, pearson_r_bench, pearson_r_ss)
        #         )
        #
        # true_df = pd.DataFrame(
        #     data=true_data,
        #     columns=[
        #         'Rivid', 'Forecast Day', 'CRPS', 'CRPS BENCH', 'CRPSS', "MAE", "MAE_BENCH", "MAESS", "MSE",
        #         "MSE_BENCH", "MSESS", "RMSE", "RMSE_BENCH", "RMSESS", "Pearson_r", "Pearson_r_BENCH", "Pearson_r_SS"
        #     ])

        true_df = pd.read_pickle(r"Test_files/Comparison_Files/benchmark_forecast_validation_df.pkl")

        # Get the computed values (Generated in setUp)
        test_df = pd.read_csv("Test_files/Forecast_analysis_test.csv")

        # Testing (Make sure it's precise to three decimals)
        pd.testing.assert_frame_equal(true_df, test_df, check_less_precise=3)

    def tearDown(self):
        os.remove(r"Test_files/Forecast_analysis_test.csv")


if __name__ == '__main__':
    unittest.main(verbosity=2)
