from setuptools import setup

with open('README.md') as f:
    README = f.read()

setup(
    name='global_forecast_validation',
    packages=['global_forecast_validation'],
    version='0.01',
    description='Routines for forecast validation on a large scale.',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Wade Roberts',
    author_email='waderoberts123@gmail.com',
    url='https://github.com/BYU-Hydroinformatics/Global_Forecast_Validation',
    keywords=['hydrology', 'forecast validation', 'global'],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
    license='MIT',
    install_requires=[
        'numpy',
        'scipy',
        'dask[complete]',
        'xarray',
        'pandas',
        'numba',
        'netcdf4',
        "progress",
    ],
    entry_points={
        'console_scripts': ['gb_fcst_val=global_forecast_validation.command_line:main', ],
    },
)
