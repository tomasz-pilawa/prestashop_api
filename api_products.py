import os
import json
from prestapyt import PrestaShopWebServiceDict

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


def test_specific_id_response(product_id=8):

    specific = prestashop.get('products', product_id)['product']
    print(specific)
    print(specific.keys())
    print(specific.values())
    print(f"\nThe name of the product is\n {specific['name']['language']['value']}")
    print(f"The reference number of the product is\n {specific['reference']}")
    print(f"The brand of the product is\n {specific['manufacturer_name']['value']}")


# test_specific_id_response(10)


def test_get_product_names_from_range(x=8, y=10):

    for x in range(x, y):
        pro = prestashop.get('products', x)['product']
        print(pro['id'])
        print(pro['name']['language']['value'])


# print(test_get_product_names_from_range(8, 11))


def get_products_indexes(n=5):

    # it's an absolute testing function - prestashop.search would be more efficient one-liner
    options = {'limit': n}
    products = prestashop.get('products', options=options)

    indexes_list = []

    for product in products['products']['product']:
        indexes_list.append(int(product['attrs']['id']))

    return indexes_list


# print(get_products_indexes(2000))


def get_next_index():
    return max(prestashop.search('products'))+1


# print(get_next_index())


def get_products(id_list=(37, 10), brand=None):         # obsolete function
    if brand:
        products_list = [prestashop.get('products', y)['product'] for y in id_list
                         if prestashop.get('products', y)['product']['manufacturer_name']['value'] == brand]
    else:
        products_list = [prestashop.get('products', y)['product'] for y in id_list]
    return products_list


def get_products_2(brand=None, to_print=0):

    with open('brands_mapped.json') as file:
        data = json.load(file)

    if brand in list(data.keys()):
        print(f"The brand exists. Processing the data...")
        indexes = data[brand]
        products = [prestashop.get('products', product_index)['product'] for product_index in indexes]
        print(f"\nThere are {len(products)} products of {brand}:\n")

        if to_print == 1:
            for product in products:
                print(product['name']['language']['value'])

        return products

    else:
        print("None brand given or the brand doesn't exist")


def update_products_json(max_products=10):

    with open('data/all_products.json', encoding='utf-8') as file:
        product_list = json.load(file)

    indexes_site = prestashop.search('products')
    indexes_data = [int(p['id']) for p in product_list]

    indexes_unique = [index for index in indexes_site if index not in indexes_data]
    indexes_selected = indexes_unique[:max_products]

    if len(indexes_selected) > 0:
        new_products_list = [prestashop.get('products', y)['product'] for y in indexes_selected]

        product_list.extend(new_products_list)

        print(f'Added {len(indexes_selected)} products. Total products in the data file now: {len(product_list)}')

        with open('data/all_products.json', 'w', encoding='utf-8') as file:
            json.dump(product_list, file)
    else:
        print(f'There were no more products to add. Total number of products is {len(product_list)}')
