import os
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
    options = {'limit': n}
    products = prestashop.get('products', options=options)

    indexes_list = []

    for product in products['products']['product']:
        indexes_list.append(int(product['attrs']['id']))

    return indexes_list


# print(get_products_indexes(2000))


def get_next_index():
    return max(get_products_indexes(5000))+1


# print(get_next_index())


def get_all_manufacturers():
    manufacturers = prestashop.get('manufacturers')
    indexes_list = []
    for manufacturer in manufacturers['manufacturers']['manufacturer']:
        indexes_list.append(int(manufacturer['attrs']['id']))
    names = [prestashop.get('manufacturers', m)['manufacturer']['name'] for m in indexes_list]
    return names


# print(get_all_manufacturers())


def get_products(a_list=(37, 10), brand=None):
    if brand:
        products_list = [prestashop.get('products', y)['product'] for y in a_list
                         if prestashop.get('products', y)['product']['manufacturer_name']['value'] == brand]
    else:
        products_list = [prestashop.get('products', y)['product'] for y in a_list]
    return products_list


extracted_products_1 = get_products(get_products_indexes(50), 'Anna Lotan')

for extr in extracted_products_1:
    print(extr['name']['language']['value'])
    print(extr['manufacturer_name']['value'])
    print(extr)
