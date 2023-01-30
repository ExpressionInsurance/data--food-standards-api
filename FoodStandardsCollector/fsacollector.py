import pandas as pd
import numpy as np
import requests
from tqdm import tqdm
import glob
import json
from pathlib import Path
import jaro

from utils.utils import find_correct_result


class FoodStandardsCollector:
    def __init__(self, path=''):
        """
        Class to take a business dataset and find the Food Standards Ratings
        :param path: File path to save the data collected
        """
        self.place_data = None
        self.file_path = path
        self._query_link = 'http://api.ratings.food.gov.uk/Establishments?name={name}&address={address}'
        self._fsa_headers = {'accept': 'application/json', 'x-api-version': '2'}
        self.df_path = ''
        self.id_col = ''
        self.name_col = ''
        self.postcode_col = ''


    def fit(self, data_path, test_sample=False, id_col='gplace_id', name_col='name', address_col='location',
            postcode_col='post_code'):
        """
        Function to prepare dataset to
        :param data_path: file path to the dataset (CSV format) that will be searched for Data from the Food Standards API
        :param test_sample: if you wish to do a test run of the data, use this field to specify the same size of the test,
        otherwise leave as False to run the full dataset
        :param id_col: name of the column that contains the ID numbers of the data
        :param name_col: name of the column that contains the business names
        :param address_col: name of column that contains the street address of the business
        :param postcode_col: name of column that contains the postcode of the business
        :return: nothing, but save the prepared data to the class ready to be requested
        """

        # Read File and drop duplicate IDs (they must be unique)
        df = pd.read_csv(data_path).drop_duplicates(subset=[id_col])

        # If test sample wanted - randomly choose those records
        if test_sample:
            df = df.sample(test_sample)

        used_ids = self.exclude_used_records()

        before = len(df)
        df = df[~df[id_col].isin(used_ids)]
        after = len(df)

        if before != after:
            print('{} records removed from data'.format(before-after))

        self.place_data = df[[id_col, name_col, address_col, postcode_col]].dropna().values

        print('{} searches to be made using Food Standards API'.format(len(self.place_data)))


    def write_raw(self):
        """
        function to hit the SerpAPI with the records we have decided to collect data for, and save the results to raw
        files (json format)
        :return: nothing but write to files
        """

        ready = input("Do you wish to continue? [y/n]\n".format(
            len(self.place_data)))
        if ready == 'y':
            for gid, name, add, pc in tqdm(self.place_data):
                json_data = self.get_rating_from_fsa_request(gid=gid, name=name, location=add, postcode=pc)
                self._write_json_to_file(results=json_data, gid=gid, name=name, location=add, postcode=pc)

    def tabulate(self, out_file_path, unmatched_file_path=False):
        """
        Function to take the raw files collected from FSA API, determine if the correct data has been found, and then
        return a CSV file of the results
        :param out_file_path: file path to save the CSV to.
        :return: nothing, but will save to files
        """
        df = self._convert_json_to_df(in_file_path=self.file_path + 'raw_data/')
        df.to_csv(self.file_path + out_file_path, index=False)


    def exclude_used_records(self):
        in_file_path = self.file_path + 'raw_data/'

        used_ids = []
        in_file_path += '/*.json'
        print('Excluding used records...')
        files = glob.glob(in_file_path)

        for file in tqdm(files):
            file = file.replace('\\', '/')
            fpath, fileformat = file.rsplit('.', 1)
            folder, gid = fpath.rsplit('/', 1)

            used_ids.append(gid)

        print('{} IDs already searched'.format(len(used_ids)))

        return used_ids


    def get_rating_from_fsa_request(self, gid, name, location, postcode):

        # Try the full postcode AND half of the postcode
        postcodes = [postcode, postcode.split(' ')[0]]

        # Try the full name, and then slowly cut down the name word by word - due to differences in names
        if name.lower()[0:4] == 'the ':
            name = name[4:].strip()

        names = [' '.join(name.split(' ')[0:i + 1]) for i in range(len(name.split(' ')))]
        names.reverse()
        names = names + [' '.join(name.split(' ')[i:]) for i in range(len(name.split(' ')))][1:]

        results = []
        for name in names:
            for pc in postcodes:
                result = self._get_json(name, pc)
                if result:
                    establishments = result.get('establishments')
                    print(name, pc)
                    if len(establishments) != 0:
                        for i, establishment in enumerate(establishments):
                            if establishment not in results:
                                results.append(establishment)
                                if i <= 10:
                                    print(establishment, '\n')
        return results


    def _write_json_to_file(self, results, gid, name, location, postcode):
        Path(self.file_path+'raw_data').mkdir(parents=True, exist_ok=True)
        file_string = self.file_path+'raw_data/{gid}.json'
        results = {
            'id': gid,
            'name': name,
            'location': location,
            'postcode': postcode,
            'results': results
        }

        with open(file_string.format(gid=gid), 'w') as file:
            json.dump(results, file)


    def _get_json(self, name, address):

        url_string = self._query_link.format(name=name, address=address)
        res = requests.get(url_string, headers=self._fsa_headers)

        try:
            res = res.json()
            return res
        except requests.exceptions.JSONDecodeError:
            return {}



    def _convert_json_to_df(self, in_file_path):
        """
        Take raw files from SerpAPI and put results into a CSV file.
        :param in_file_path: file path to find the raw files
        :return: dataframe
        """
        all_data = []
        in_file_path += '/*.json'
        print('Tabulating...')
        files = glob.glob(in_file_path)

        total = len(files)
        success = 0

        for file in tqdm(files):
            file = file.replace('\\', '/')
            fpath, fileformat = file.rsplit('.', 1)
            folder, gid = fpath.rsplit('/', 1)

            data = json.load(open(file))

            result, confidence = find_correct_result(data=data, gid=gid)

            if type(result) == dict:

                # Pull out relevant results
                result = {
                    'id1': gid,
                    'FHRSID': result.get('FHRSID'),
                    'BusinessName': result.get('BusinessName'),
                    'AddressLine1': result.get('AddressLine1'),
                    'AddressLine2': result.get('AddressLine2'),
                    'AddressLine3': result.get('AddressLine3'),
                    'AddressLine4': result.get('AddressLine4'),
                    'PostCode': result.get('PostCode'),
                    'RatingValue': result.get('RatingValue'),
                    'RatingDate': result.get('RatingDate'),
                    'Hygiene': result.get('scores', {}).get('Hygiene'),
                    'Structural': result.get('scores', {}).get('Structural'),
                    'ConfidenceInManagement': result.get('scores', {}).get('ConfidenceInManagement')
                }
                all_data.append(result)

        all_data = pd.DataFrame(all_data)

        return all_data



