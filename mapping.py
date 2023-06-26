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
    category_names = [[prestashop.get('categories', m)['category']['name']['language']['value'],
                       prestashop.get('categories', m)['category']['id_parent']] for m in category_ids]

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


def update_products_json(max_products=10, brand_update=None):

    with open('data/all_products.json', encoding='utf-8') as file:
        product_list = json.load(file)

    indexes_site = prestashop.search('products')
    indexes_data = [int(p['id']) for p in product_list]

    indexes_unique = [index for index in indexes_site if index not in indexes_data]
    indexes_selected = indexes_unique[:max_products]

    if brand_update:
        indexes_brand = [int(p['id']) for p in product_list if brand_update == p['manufacturer_name']['value']]
        updated_products_list = [prestashop.get('products', x)['product'] for x in indexes_brand]

        for updated_product in updated_products_list:
            for i, existing_product in enumerate(product_list):
                if int(existing_product['id']) == updated_product['id']:
                    product_list[i] = updated_product
                    break
        print(f'Updated {len(updated_products_list)} products for brand "{brand_update}"')
    else:
        print(f'There were no products to update for brand "{brand_update}"')

    if len(indexes_selected) > 0:
        new_products_list = [prestashop.get('products', y)['product'] for y in indexes_selected]

        product_list.extend(new_products_list)

        print(f'Added {len(indexes_selected)} products. Total products in the data file now: {len(product_list)}')

        with open('data/all_products.json', 'w', encoding='utf-8') as file:
            json.dump(product_list, file)
    else:
        print(f'There were no more new products to add. Total number of products now is {len(product_list)}')
