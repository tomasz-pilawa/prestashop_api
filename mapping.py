import os
import json
from prestapyt import PrestaShopWebServiceDict

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


def get_init_brand_dict():

    indexes = prestashop.search('products')

    products_list = [prestashop.get('products', y)['product'] for y in indexes]
    indexes_used = []
    brands_used = []

    for product in products_list:
        indexes_used.append(product['id'])
        if not product['manufacturer_name']['value']:
            product['manufacturer_name']['value'] = 'Z_MISSING'
        brands_used.append(product['manufacturer_name']['value'])

    result = {}
    for brand, product in zip(brands_used, indexes_used):
        result.setdefault(brand, []).append(int(product))
    result['indexes_used'] = indexes_used

    with open('brands_mapped.json', 'w') as file:
        json.dump(result, file)

    print(result)

    return result


# print(get_all_manufacturers())


def get_manufacturers_dict():

    manufacturer_ids = prestashop.search('manufacturers')
    manufacturer_names = [prestashop.get('manufacturers', m)['manufacturer']['name'] for m in manufacturer_ids]

    manufacturer_dict = dict(zip(manufacturer_names, manufacturer_ids))

    with open('manufacturers_dict.json', 'w') as file:
        json.dump(manufacturer_dict, file)

    return manufacturer_dict


def get_categories_dict():

    category_ids = prestashop.search('categories')
    category_names = [prestashop.get('categories', m)['category']['name']['language']['value'] for m in category_ids]

    category_dict = dict(zip(category_ids, category_names))

    with open('categories_dict.json', 'w') as file:
        json.dump(category_dict, file)

    return category_dict


def get_init_sku_dict():

    indexes = prestashop.search('products')

    products_list = [prestashop.get('products', y)['product'] for y in indexes]
    sku_list = []
    brands = []

    for product in products_list:
        sku_list.append(product['reference'])
        if not product['manufacturer_name']['value']:
            product['manufacturer_name']['value'] = 'Z_MISSING'
        brands.append(product['manufacturer_name']['value'])

    result = {}
    for brand, product in zip(brands, sku_list):
        result.setdefault(brand, []).append(product)
    result['indexes_used'] = sku_list

    with open('sku_mapped.json', 'w') as file:
        json.dump(result, file)

    return result

