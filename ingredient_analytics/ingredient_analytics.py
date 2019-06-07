# python 3.6

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn
import json
from pathlib2 import Path
import requests
import time
import itertools

seaborn.set_context(context='talk')

WORKING_DIRECTORY = Path(os.path.abspath(__file__)).parent
GRAPHS_DIRECTORY = os.path.join(WORKING_DIRECTORY, 'graphs_directory')
if not os.path.isdir(GRAPHS_DIRECTORY):
    os.makedirs(GRAPHS_DIRECTORY)


class _QueryOpenFDA:
    """
    Simple wrapper around OpenFDA API. This class is not to be used
    as a final object but is designed to be subclassed. See the :py:class:`IngredientAnalytics`
    class for an example.

    Subclasses must implement the :py:meth:`extract_relevant_data` method.

    """

    _max_limit = 99

    def __init__(self, url):
        """

        Args:
            url (str): valid url for querying the OpenFDA API.
        """
        self.url = url

        self.num_full_requests = self._compute_chuncksizes()['num_full_requests']
        self.size_of_last_request = self._compute_chuncksizes()['size_of_last_request']

    def _number_of_search_results(self):
        """
        Gets number of records that can be returned with the current url

        Returns (int): number of items returned by search

        """
        response = requests.get(self.url)
        return json.loads(response.content)['meta']['results']['total']

    def _compute_chuncksizes(self):
        """
        Work out how many times we need to use request to get
        all of the search results, given that the API caps at 99.

        Returns (int):

        """
        number_of_full_requests = self._number_of_search_results() // self._max_limit
        size_of_last_request = self._number_of_search_results() % self._max_limit
        assert number_of_full_requests * self._max_limit + size_of_last_request == self._number_of_search_results()
        return {
            'num_full_requests': number_of_full_requests,
            'size_of_last_request': size_of_last_request
        }

    def _fetch_data(self):
        """
        Query the openFDA API using the url specified as argument. If >99
        items in a search, then perform multiple requests.

        Returns (pandas.DataFrame): All results

        """
        l = []
        for req in range(self.num_full_requests):
            time.sleep(5.0)
            start = req * self._max_limit
            end = start + self._max_limit
            print(f'collecting {start} to {end} of {self._number_of_search_results()}')
            r = requests.get(f'{self.url}&skip={start}&limit=99').json()
            try:
                l.append(self.extract_relevant_data(r))
            except NotImplementedError:
                raise NotImplementedError('You must override the "extract_relevant_data" method')

        if self.size_of_last_request != 0:
            start = self._number_of_search_results() - self.size_of_last_request
            last_request = requests.get(
                f'{self.url}&skip={start}&limit={self.size_of_last_request}').json()
            l.append(self.extract_relevant_data(last_request))

        return pd.concat(l)

    def extract_relevant_data(self, r):
        """
        Override in subclass. Implement method that extracts the data you need
        from the query. Method must take the return value r of a requests.get().json
        call, iterate over the 'results' key and return a pandas.DataFrame containing
        the data you wish to keep.

        Returns:

        """
        raise NotImplementedError


class IngredientAnalytics(_QueryOpenFDA):
    """
    Implementation for part A.
    """

    def extract_relevant_data(self, r):
        """
        Extract manufacturer name, drug name, the number of drug ingredients
        and year from a search
        Args:
            r (dict, jsonified): A single result that is returned from the request.get().json.
                                 See also :py:meth:`self._fetch_data`.

        Returns:

        """
        l = []
        for i in r['results']:
            effective_time = int(i['effective_time'][:-4])

            if i['openfda'] == {}:
                continue
            manufacturer_name = i['openfda']['manufacturer_name']
            generic_name = i['openfda']['generic_name']
            spl_product_data_elements = len(i['spl_product_data_elements'][0].split(' '))

            l.append([generic_name, effective_time, spl_product_data_elements, manufacturer_name])
        return pd.DataFrame(l, columns=['generic_name', 'year', 'num_ingredients', 'manufacturer'])

    def av_number_ingredients_per_year(self):
        """
        Calculates the average number of ingredients in AstraZeneca products per year

        Returns (pandas.DataFrame): columns: year, drugs, average

        """
        data = self._fetch_data()
        names = {}
        for label, df in data.groupby(by='year'):
            n = df[df['year'] == label]['generic_name'].values
            names[label] = [[i for i in itertools.chain(*n)]]
        drug_names_df = pd.DataFrame(names).transpose()
        mean = data.groupby(by='year').mean()

        df = mean.merge(drug_names_df, left_index=True, right_index=True)
        df.columns = ['avg_number_of_ingredients', 'drug_names']
        df = df[['drug_names', 'avg_number_of_ingredients']]
        return df

    def plot(self, cls=seaborn.lineplot, savefig=False):
        """
        plots the average number of ingredients per year in astrazenica drugs.
        Args:
            cls (class): either seaborn.lineplot or seaborn.barplot
            savefig (bool): Save to file when True and show when False

        Returns (None):
        """
        if cls.__name__ not in ['lineplot', 'barplot']:
            raise TypeError('Currently only support seaborn.lineplot or seaborn.barplot')
        data = self._fetch_data()
        fig = plt.figure()
        cls(data=data, y='num_ingredients', x='year')
        data = self._fetch_data()
        fig = plt.figure()
        seaborn.lineplot(data=data, y='num_ingredients', x='year')
        seaborn.despine(fig=fig, top=True, right=True)
        plt.title('Number of ingredients in AstraZeneca products per year')

        plt.xlabel('Number of Ingredients')
        plt.ylabel('Year')

        if savefig:
            fname = os.path.join(GRAPHS_DIRECTORY, 'number_of_ingredients_per_year_{}.png'.format(cls.__name__))
            plt.savefig(fname, dpi=300, bbox_inches='tight')
            print('figure save to "{}"'.format(fname))
        else:
            plt.show()


class IngredientAndRouteAnalytics(_QueryOpenFDA):
    """
    Implementation for part B.
    """

    def extract_relevant_data(self, r):
        l = []
        for i in r['results']:
            effective_time = int(i['effective_time'][:-4])

            if i['openfda'] == {}:
                continue
            manufacturer_name = i['openfda']['manufacturer_name']

            # handle situation when the route key is not present
            try:
                route = i['openfda']['route']
                if isinstance(route, list) and len(route) == 1:
                    route = route[0]
            except KeyError:
                route = np.nan
            generic_name = i['openfda']['generic_name']
            spl_product_data_elements = len(i['spl_product_data_elements'][0].split(' '))

            l.append([generic_name, route, effective_time, spl_product_data_elements, manufacturer_name])
        return pd.DataFrame(l, columns=['generic_name', 'route', 'year', 'num_ingredients', 'manufacturer'])

    def av_number_ingredients_per_year_per_route(self):
        """
        Calculates the average number of ingredients in AstraZeneca products per
        year and per method of administration

        Returns (pandas.DataFrame): columns: year, route, drugs, average

        Returns:

        """
        data = self._fetch_data()
        names = {}
        for label, df in data.groupby(by=['year', 'route']):
            n = df[(df['year'] == label[0]) & (df['route'] == label[1])]['generic_name'].values
            names[label] = [[i for i in itertools.chain(*n)]]
        drug_names_df = pd.DataFrame(names).transpose()
        drug_names_df.index.names = ['year', 'route']
        mean = data.groupby(by=['year', 'route']).mean()
        drug_names_df.columns = ['drug_name']

        df = pd.concat([mean, drug_names_df], axis=1)
        df = df[['drug_name', 'num_ingredients']]
        df.rename(columns={'num_ingredients': 'avg_number_of_ingredients'}, inplace=True)
        return df

    def plot(self, cls=seaborn.lineplot, savefig=False):
        """
        plots the average number of ingredients per year per route in astrazenica drugs.
        Args:
            cls (class): either seaborn.lineplot or seaborn.barplot
            savefig (bool): Save to file when True and show when False

        Returns (None):

        """
        if cls.__name__ not in ['lineplot', 'barplot']:
            raise TypeError('Currently only support seaborn.lineplot or seaborn.barplot')
        data = self._fetch_data()
        fig = plt.figure()
        cls(data=data, y='num_ingredients', x='year', hue='route')
        seaborn.despine(fig=fig, top=True, right=True)
        plt.title('Number of ingredients in AstraZeneca \nproducts per year per administration route')
        plt.legend(loc=(1, 0.5))
        plt.xlabel('Number of Ingredients')
        plt.ylabel('Year')

        if savefig:
            fname = os.path.join(GRAPHS_DIRECTORY, 'number_of_ingredients_per_year_per_route_{}.png'.format(cls.__name__))
            plt.savefig(fname, dpi=300, bbox_inches='tight')
            print('figure save to "{}"'.format(fname))

        else:
            plt.show()


if __name__ == '__main__':
    query_url = r'https://api.fda.gov/drug/label.json?search=openfda.manufacturer_name:"AstraZeneca"'

    # task 1
    ingredient_analytics = IngredientAnalytics(query_url)
    print(ingredient_analytics.av_number_ingredients_per_year())

    ingredient_analytics.plot(seaborn.lineplot, True)
    ingredient_analytics.plot(seaborn.barplot, True)

    # task 2
    ingredient_and_route_analytics = IngredientAndRouteAnalytics(query_url)
    print(ingredient_and_route_analytics.av_number_ingredients_per_year_per_route())

    ingredient_and_route_analytics.plot(seaborn.lineplot, savefig=True)
    ingredient_and_route_analytics.plot(seaborn.barplot, savefig=True)

"""
reflections
-----------
- This implementation contains a reasonable amount of duplicated code. It would be 
  better to find a single more flexible class that was capable of performing both 
  the functions of IngredientAnalytics adnd IngredientAndRouteAnalytics. 
- The query being used to test this code only returned 43 results. Other similar queries 
  returned more (>500) but closer inspection revealed the drugs were sold by companies 
  other than AstraZenica. With more time, the API would have been more appropriately explored 



Answers to other questions
--------------------------

How would you code a model to predict the number of ingredients for next year? Note: Your predictions don't have to be good !

- Assuming the search url was modified so that it returned much more than 43 results, i.e. so that we  have enough 
  data to train a model, we could try using a recurrent neural network which are good for 
  predicting sequences. As a first take I would use keras to implement a LSTM architecture and train 
  by minimizing the root mean squared error. The model would be evaluated using both a validation dataset (during training) 
  and a test set (after training). 

Could you find the most common drug interactions for AstraZeneca medicines?

- I would get the set of all AstraZeneca medicines and then the subset of pairs of compounds that interact. Then I'd 
  find the pair of compounds that are present in most drugs. 


How would you deploy your analysis/model as a tool that other users can use?

- Could be a library, much like this one. 
- Or could be an app or some other form of software that has the model embedded within.  
- The model would have to be presented with a year (or year and route) as input and the model 
  would predict the number of ingredients AztraZeneca uses per year (or per year and route).
"""
