import pandas as pd
from pathlib import Path

from FoodStandardsCollector.fsacollector import FoodStandardsCollector


if __name__ == '__main__':

    date = '20220623_4'

    # Use a run number to run a certain split of the file on multiple machines using
    # run_number = 1
    # run_number = input('What is the run number?\n')

    # Bring in Class
    # run_path = 'Collection/fsa_update_20221025/run_{}/'.format(run_number)
    run_path = 'Collection/fsa_main_update_{}/'.format(date)
    Path(run_path).mkdir(parents=True, exist_ok=True)
    collector = FoodStandardsCollector(path=run_path)

    # Path of the data you want to use to query SerpAPI.
    # path = 'data/fsa_update_20221025/restaurants/restaurants_{}.csv'.format(run_number)
    data_path = 'data/fsa_update_{}/new_data_{}.csv'.format(date, date)

    # print('Run path will be {}'.format(run_path))
    print('Data file used is {}'.format(data_path))

    # format data to search using Serp
    #collector.fit(test_sample=False, data_path=data_path, id_col='gplace_id', address_col='location',
    #              name_col='name',  postcode_col='post_code')

    # run the searches and collect the raw data to JSON format.
    #collector.write_raw()

    # return a csv of the results from the searches.
    # out_path = 'fsa_data_collected_{}.csv'.format(run_number)
    out_path = 'fsa_data_collected.csv'
    collector.tabulate(out_file_path=out_path)  # , unmatched_file_path=unmatched_path
