import unittest

from .ingredient_analytics import *


class IngredientAnalyticTests(unittest.TestCase):

    def setUp(self):
        self.url = r'https://api.fda.gov/drug/label.json?search=openfda.manufacturer_name:"AstraZeneca"'

    def tearDown(self):
        pass

    def test_fetch_data(self):
        q = IngredientAnalytics(self.url)
        df = q._fetch_data()
        expected = 43
        self.assertEqual(expected, df.shape[0])

    def test_plot(self):
        q = IngredientAnalytics(self.url)
        q.barplot(savefig=True)
        fname = os.path.join(GRAPHS_DIRECTORY, 'number_of_ingredients_per_year.png')
        self.assertTrue(os.path.isfile(fname))

    def test_average_num_per_year(self):
        q = IngredientAnalytics(self.url)
        expected = 46.666667
        actual = q.av_number_ingredients_per_year().loc[2017]['avg_number_of_ingredients']
        self.assertAlmostEqual(expected, actual, 4)


class IngredientAndRouteAnalyticsTests(unittest.TestCase):

    def setUp(self):
        self.url = r'https://api.fda.gov/drug/label.json?search=openfda.manufacturer_name:"AstraZeneca"'

    def tearDown(self):
        pass

    def test_fetch_data(self):
        q = IngredientAndRouteAnalytics(self.url)
        df = q._fetch_data()
        expected = 'ORAL'
        self.assertEqual(expected, df.iloc[6]['route'])

    def test_plot(self):
        q = IngredientAndRouteAnalytics(self.url)
        q.plot(savefig=True)
        fname = os.path.join(GRAPHS_DIRECTORY, 'number_of_ingredients_per_year_per_route.png')
        self.assertTrue(os.path.isfile(fname))

    def test_average_num_per_year_per_route(self):
        q = IngredientAndRouteAnalytics(self.url)
        expected = 12.0
        actual = q.av_number_ingredients_per_year_per_route().loc[2017, 'SUBCUTANEOUS']['avg_number_of_ingredients']
        self.assertAlmostEqual(expected, actual, 4)


if __name__ == '__main__':
    unittest.main()
