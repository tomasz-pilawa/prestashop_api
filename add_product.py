import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


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

    with open('default_product_values.json') as def_file:
        default_values = json.load(def_file)

    data.update(default_values)

    data.pop('manufacturer_name')

    for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
        data[x] = {'language': {'attrs': {'id': '2'}, 'value': data[x]}}

    print('Inserting the product...')

    product_info = {'product': data}
    print(product_info)
    prestashop.add('products', product_info)

    return data


