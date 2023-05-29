import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


product_1 = 'random_product.csv'


def add_product_from_csv(product):

    with open(product) as file:
        reader = csv.reader(file)
        header = next(reader)
        row = next(reader)
        data = dict(zip(header, row))

    with open('manufacturers_dict.json') as man_file:
        id_manufacturer = json.load(man_file)[data['manufacturer_name']]

    data['id_manufacturer'] = id_manufacturer
    data['wholesale_price'] = str(round(int(data['price'])/1.87, 2))
    data['link_rewrite'] = data['name'].lower().replace(' ', '-')

    return data


print(add_product_from_csv(product_1))
