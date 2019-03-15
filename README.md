# Global_Forecast_Validation

Python solution to run large scale forecast validation using data stored in NetCDF format. This tool is meant to be 
used with RAPIDpy, and should not be used with NetCDF files formatted in ways different than the RAPIDpy output.

## Installation 
Dependencies are listed in Requirements.txt, the following code will add them to an existing conda environment (make 
sure you are in the same directory as the Requirements.txt folder when you type this).

`conda install --file Requirements.txt`

## Testing
Once the dependencies are installed, it is highly recommeded to run the testing suite contained in the `tests.py` file.
Simply activate the environment and run the file to check if all the tests pass. If not, there may
be an issue with updates to the dependencies and an issue should be submitted on Github.