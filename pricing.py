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


# fix_prices(limit=800, file='new_prices_urodama_07_2023.xml')


def fix_stock(file_old=None, file_new=None):

    prestashop = PrestaShopWebServiceDict(api_url_urodama, api_key_urodama)

    tree_old = ET.parse(f'data/{file_old}')
    root_old = tree_old.getroot()
    all_products_old = root_old.findall('o')
    indexes_old = [int(p.get('id')) for p in all_products_old]

    tree_new = ET.parse(f'data/{file_new}')
    root_new = tree_new.getroot()
    all_products_new = root_new.findall('o')
    indexes_new = [int(p.get('id')) for p in all_products_new]

    indexes_to_disable = [i for i in indexes_new if i not in indexes_old]
    products_to_disable = [p for p in all_products_new if int(p.get('id')) in indexes_to_disable]

    for p in products_to_disable:
        p_id = int(p.get('id'))

        product = prestashop.get('products', p_id)

        product['product']['active'] = 0
        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')

        # if int(product['product']['position_in_category']['value']) < 1:
        #     product['product']['position_in_category']['value'] = str(1)

        print(product['product'])

        prestashop.edit('products', product)


# fix_stock(file_old='new_prices_urodama_07_2023.xml', file_new='ceneo_urodama_after_update_too_many.xml')
