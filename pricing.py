import os
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET


api_url_urodama = os.getenv('urodama_link')
api_key_urodama = os.getenv('urodama_pass')


def fix_prices(limit=2, file=None):

    prestashop = PrestaShopWebServiceDict(api_url_urodama, api_key_urodama)

    tree = ET.parse(f'data/{file}')
    root = tree.getroot()

    all_products = root.findall('o')

    for p in all_products[:limit]:
        p_name = p.find('name').text
        p_id = int(p.get('id'))
        p_price = p.get('price')

        product = prestashop.get('products', p_id)

        product['product']['price'] = p_price

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')

        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        product['product']['price'] = p_price
        print(product['product'])

        prestashop.edit('products', product)


fix_prices(limit=800, file='new_prices_urodama_07_2023.xml')
