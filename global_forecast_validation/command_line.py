import argparse
from global_forecast_validation.compress_netcdf import compress_netcfd
from global_forecast_validation.validate_forecasts import compute_all
from global_forecast_validation.extract_data import extract_by_rivid


def compress_netcdf_cli(args):
    folder_path = args.folder_path
    out_folder = args.out_folder
    file_name = args.file_name

    compress_netcfd(folder_path, out_folder, file_name)


def validate_cli(args):
    work_dir = args.work_dir
    out_path = args.out_path
    memory_to_allocate_gb = args.memory
    starting_date = args.start_date
    ending_date = args.end_date

    compute_all(work_dir, out_path, memory_to_allocate_gb, starting_date, ending_date)


def extract_cli(args):
    folder_path = args.folder_path
    outpath = args.outpath
    rivid = 192451

    extract_by_rivid(rivid, folder_path, outpath)


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title='Commands', dest='require at least one argument')
    subparsers.required = True

    # Setup compress command
    compress_parser = subparsers.add_parser(
        'compress',
        help='Takes 52 separate NetCDF forecast files and combines them into one compact NetCDF file with only daily values'
    )
    compress_parser.add_argument(
        'folder_path', help='The path to the directory containing the forecast files', type=str
    )
    compress_parser.add_argument(
        'out_folder', help='The path to the directory that you want the more compact NetCDF file in.', type=str
    )
    compress_parser.add_argument(
        'file_name', help='The name of the region. For example, if the files followed the pattern of '
                          '"Qout_africa_continental_1.nc, this argument would be "Qout_africa_continental"', type=str
    )
    compress_parser.set_defaults(func=compress_netcdf_cli)

    # Setup validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Takes a directory of NetCDf files created with the compress command and performs forecasts validation with '
             'them. The results of the analysis are stored in a csv. WARNING: The netcdf files must be consecutive daily '
             'values, else the results will be wrong.'
    )
    validate_parser.add_argument(
        'work_dir', type=str,
        help='The directory that contains all of the forecast files that were created with the compress_netcdf '
             'function. Make sure that this directory only contains the compressed forecast files.'
    )
    validate_parser.add_argument(
        "out_path", type=str, help="The path where the resulting CSV of results should be stored. Include the file name "
                                   "in this path! For example, if I wanted the file to be stored in the same directory as "
                                   "I ran the script in, I would simply set this parameter to be the name of the file (ie "
                                   "Skill_Scores.csv)."
    )
    validate_parser.add_argument(
        "memory", type=float, help="Indicates the memory that you would like to be allocated on the computer when "
                                   "running the program. It is highly recommended to be conservative in this number as "
                                   "slightly more memory may be consumed (maybe up to half a gig in very large regions)."
    )
    validate_parser.add_argument(
        '-sd', '--start_date', type=str, help='(Optional) The starting date of the analysis formatted as YYYY-MM-DD '
                                              '(i.e. January 2, 2019 would be 2019-01-02).'
    )
    validate_parser.add_argument(
        '-ed', '--end_date', type=str, help='(Optional) The ending date of the analysis formatted as YYYY-MM-DD (i.e. '
                                            'January 2, 2019 would be 2019-01-02).'
    )
    validate_parser.set_defaults(func=validate_cli)

    # Setup extract command
    extract_parser = subparsers.add_parser(
        'extract',
        help='Extracts data from a folder with NetCDF forecast files (generated with the compress_netcdf function) into '
             'CSV files in the given path'
    )
    extract_parser.add_argument(
        'rivid', type=int,
        help='The rivid (COMID) of the desired stream to extract data for.'
    )
    extract_parser.add_argument(
        'folder_path', type=str,
        help='The path to the folder containing the forecast NetCDF files.'
    )
    extract_parser.add_argument(
        'outpath', type=str,
        help='The path to the directory that you would like to write the CSV files to.'
    )
    extract_parser.set_defaults(func=extract_cli)

    args = parser.parse_args()

    args.func(args)
