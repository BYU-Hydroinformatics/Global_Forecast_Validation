import argparse
from compress_netcdf import compress_netcfd


def compress_netcdf_cli(args):

    folder_path = args.folder_path
    out_folder = args.out_folder
    file_name = args.file_name

    compress_netcfd(folder_path, out_folder, file_name)


def extract_data_cli(args):
    pass


# def main():
parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(title='Commands', dest='require at least one argument')
subparsers.required = True

# Setup square command
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
args = parser.parse_args()

args.func(args)
