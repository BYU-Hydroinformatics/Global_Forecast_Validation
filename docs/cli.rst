Command Line Interface
======================

The global-forecast-validation package comes with a command line interface included in the installation.
It can be used by activating the environment that global-forecast-validation was installed in and using
the command `gb_fcst_val`. Seeing a list of all of the available commands in the command line interface
simply requires the following command in the terminal::

    gb_fcst_val -h

This will produce the following::

    usage: gb_fcst_val [-h] {compress,validate,extract} ...

    optional arguments:
      -h, --help            show this help message and exit

    Commands:
      {compress,validate,extract}
        compress            Takes 52 separate NetCDF forecast files and combines
                            them into one compact NetCDF file with only daily
                            values
        validate            Takes a directory of NetCDf files created with the
                            compress command and performs forecasts validation
                            with them. The results of the analysis are stored in a
                            csv. WARNING: The netcdf files must be consecutive
                            daily values, else the results will be wrong.
        extract             Extracts data from a folder with NetCDF forecast files
                            (generated with the compress_netcdf function) into CSV
                            files in the given path

To then see the arguments for a specific argument, simply type the following in the command line::

    gb_fcst_val compress -h

Which then produces::

    usage: gb_fcst_val compress [-h] folder_path out_folder file_name

    positional arguments:
      folder_path  The path to the directory containing the forecast files
      out_folder   The path to the directory that you want the more compact NetCDF
                   file in.
      file_name    The name of the region. For example, if the files followed the
                   pattern of "Qout_africa_continental_1.nc, this argument would
                   be "Qout_africa_continental"

    optional arguments:
      -h, --help   show this help message and exit

After this, simply enter the required arguments (and optional arguments if desired) and the functions will
run the same as if you used them in a python script.