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

WORKING_DIRECTORY = Path(os.path.abspath(__file__)).parents[1]
GRAPHS_DIRECTORY = os.path.join(WORKING_DIRECTORY, 'graphs')
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

    def plot(self, x_name, y_name, cls=seaborn.lineplot, fname=None,
             title=None, xlabel=None, ylabel=None, savefig=False, legend=False,
             **kwargs):
        """

        Args:
            x_name  (str)      : name of variable on x-axis, must be column in dataframe returned by :py:meth:`extract_relevant_data`
            y_name  (str)      : name of variable of y-axis, must be column in dataframe returned by :py:meth:`extract_relevant_data`
            cls     (callable) : either seaborn.lineplot or seaborn.barplot
            savefig (bool)     : Save to file or not
            fname   (str)      : file name to save to for when savefig=True
            title   (str)      : title for plot
            xlabel  (str)      : xlabel for plot
            ylabel  (str)      : ylabel for plot
            legend  (bool)      : legend
            **kwargs           : unpacked and passed to cls

        Returns : None

        """
        if cls.__name__ not in ['lineplot', 'barplot']:
            raise TypeError('Currently only support seaborn.lineplot or seaborn.barplot')

        data = self._fetch_data()

        fig = plt.figure()
        cls(data=data, y=y_name, x=x_name, **kwargs)
        seaborn.despine(fig=fig, top=True, right=True)

        if title:
            plt.title(title)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
        if legend:
            plt.legend(loc=(1, 0.1))

        if savefig:
            if fname is None:
                raise ValueError('Give argument to fname kwarg to save figure.')
            plt.savefig(fname, dpi=300, bbox_inches='tight')
            print('figure save to "{}"'.format(fname))
        else:
            plt.show()

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
            spl_product_data_elements = len(i['spl_product_data_elements'][0].split(','))

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
            spl_product_data_elements = len(i['spl_product_data_elements'][0].split(','))

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



if __name__ == '__main__':
    query_url = r'https://api.fda.gov/drug/label.json?search=openfda.manufacturer_name:"AstraZeneca"'

    # task 1
    ingredient_analytics = IngredientAnalytics(query_url)
    print(ingredient_analytics.av_number_ingredients_per_year())

    for i in [seaborn.lineplot, seaborn.barplot]:
        ingredient_analytics.plot(
            x_name='year', y_name='num_ingredients',
            savefig=True,
            fname=os.path.join(GRAPHS_DIRECTORY, 'number_of_ingredients_per_year_{}.png'.format(i.__name__)),
            cls=i, title='Number of Ingredients in AstraZeneca Drugs per year',
            xlabel='year', ylabel='Number of ingredients'
        )

    # task 2
    ingredient_and_route_analytics = IngredientAndRouteAnalytics(query_url)
    print(ingredient_and_route_analytics.av_number_ingredients_per_year_per_route())

    for i in [seaborn.lineplot, seaborn.barplot]:
        ingredient_and_route_analytics.plot(
            x_name='year', y_name='num_ingredients',
            savefig=True,
            fname=os.path.join(GRAPHS_DIRECTORY, 'number_of_ingredients_per_year_per_route_{}.png'.format(i.__name__)),
            cls=i, title='Number of Ingredients in AstraZeneca \nDrugs per Year per Route',
            xlabel='year', ylabel='Number of ingredients', hue='route', legend=True
        )


"""
Reflections
-----------
- It would be nice to simply specify fields as parameters and use the same class for all 
  OpenFDA searches. However, the subclass system I've put in place here is more appropriate 
  because the data return for each search requires some post-retrieval processing. 
- The query being used to test this code only returned 43 results. Other similar queries 
  returned more (>500) but closer inspection revealed the drugs were manufactured by companies 
  other than AstraZeneca. 
- With more time, and perhaps outside of a 'challenge' setting, I would have
  made some effort to clarify the meaning of the phrase "AstraZeneca medinine". Does it mean those sold 
  by AZ? Produced by AZ? Manafactured by AZ? Researched by AZ? 


Answers to other questions
--------------------------

How would you code a model to predict the number of ingredients for next year? Note: Your predictions don't have to be good !

- I think this is probably quite a difficult task because I do not expect the number of ingredients 
  contained in a drug to be correlated with time. Drug ingredients depend on the mechanistic requirements 
  of a therapy, it doesn't necessarily matter *when* the drug is produced. 
  - Route of administration may be better predictor for number of ingredients in a drug, given that there 
    seems to be significantly more ingredients in oral drugs than other drugs. However, I still think that 
    there may be other predictors that would suit the problem better, i.e. disease type maybe?  
- If after expressing my concerns regarding the problem definition, I was still asked to try and 
  use year to predict number of medicines in AstraZeneca medicines, I would first clarify the meaning
  of the phrase "AstraZeneca medicine" and to ensure i had the correct data. Then I would try to 
  model a trend (assuming one can be found) with an autoregressive model.
  Failing that we could try a recurrent neural network with (maybe) a LSTM architecture, 
  using keras for a simple first implementation. Note however, it would be 
  important to ensure we had much more than the 43 data points for training/testing. 

Could you find the most common drug interactions for AstraZeneca medicines?

- I would get the set of all AstraZeneca medicines and then the subset of pairs of compounds that interact. Then I'd 
  find the pair of compounds that occur most frequently in AstraZeneca drugs. 


How would you deploy your analysis/model as a tool that other users can use?

- Could be a library/package/module, an app, command line program or full blown software. All of these could 
  implement an interface that enables users to enter their inputs (i.e. their new instances of 
  year or year and route of administration) to a copy of the fully trained model. 
  The model would be evaluated and the output (i.e. predictions) returned to the 
  user.
  - It would be interesting to implement a piece of software (like a platform) that contains many such models with a UI. 
    This model would then be just one of a list of useful models that can be used to make a variety of predictions

"""
