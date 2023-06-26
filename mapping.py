import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode


api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


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


def update_brands_dict():

    idx = prestashop.search('products')

    products_list = [prestashop.get('products', y)['product'] for y in idx[:10]]
    indexes = []
    skus = []
    brands = []

    for product in products_list:
        indexes.append(product['id'])
        skus.append(product['reference'])
        if not product['manufacturer_name']['value']:
            product['manufacturer_name']['value'] = 'Z_MISSING'
        brands.append(product['manufacturer_name']['value'])

    brands_dict ={}

    indexes_dict = {}
    for brand, product in zip(brands, indexes):
        indexes_dict.setdefault(brand, []).append(int(product))
    brands_dict['indexes'] = indexes_dict

    skus_dict = {}
    for brand, product in zip(brands, skus):
        skus_dict.setdefault(brand, []).append(product)
    brands_dict['skus'] = skus_dict

    brands_dict['all_sku'] = skus
    brands_dict['all_index'] = indexes

    with open('data/brands_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(brands_dict, file)


def create_category_dicts(csv_name='cats_pairing_init.csv', version='0', update_classification_dict=0):

    version = str(version)
    data = []

    with open(f'data/{csv_name}', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)

    json_name = f"{csv_name.split('_')[0]}_{csv_name.split('_')[1]}_v_{version}.json"

    with open(f'data/{json_name}', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print('JSON file saved successfully')

    if update_classification_dict == 1:

        categories = {
            'cat_main': [],
            'cat_face_form': [],
            'cat_face_action': [],
            'cat_body': [],
            'cat_hair': [],
            'cat_random': [],
            'cat_other': [],
            'cat_old': []
        }

        for row in data:

            category_type = row['Type']
            category_name = row['NameNew']
            categories['cat_old'].append(row['NameOld'])

            if category_type == 'main':
                categories['cat_main'].append(category_name)
            elif category_type == 'face_form':
                categories['cat_face_form'].append(category_name)
            elif category_type == 'face_action':
                categories['cat_face_action'].append(category_name)
            elif category_type == 'body':
                categories['cat_body'].append(category_name)
            elif category_type == 'hair':
                categories['cat_hair'].append(category_name)
            elif category_type == 'random':
                categories['cat_random'].append(category_name)
            else:
                categories['cat_other'].append(category_name)

        categories['cat_old'] = [c for c in categories['cat_old'] if c not in ['None']]

        cats_classify_filename = f'categories_to_classify_{version}.json'

        with open(f'data/{cats_classify_filename}', 'w', encoding='utf-8') as json_file:
            json.dump(categories, json_file, ensure_ascii=False)

        print('Categories to Clasify dumped into JSON too')


def set_categories_tree(changes_file=None):

    with open(f'data/{changes_file}', encoding='utf-8') as file:
        changes = json.load(file)

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    name_change = [n for n in changes if n['ChangeType'] in ['Name', 'NameParent']]

    for cat in name_change:
        cat_to_modify = prestashop.get('categories', cat['ID'])
        cat_to_modify['category']['name']['language']['value'] = cat['NameNew']

        link_rewritten = unidecode(cat_to_modify['category']['name']['language']['value'].lower().replace(' ', '-'))
        cat_to_modify['category']['link_rewrite']['language']['value'] = link_rewritten

        cat_to_modify['category'].pop('level_depth')
        cat_to_modify['category'].pop('nb_products_recursive')

        prestashop.edit('categories', cat_to_modify)

    parent_change = [p for p in changes if p['ChangeType'] in ['NameParent', 'OrderRemove']]

    for cat in parent_change:
        cat_to_modify = prestashop.get('categories', cat['ID'])
        cat_to_modify['category']['id_parent'] = cat['ParentNew']

        link_rewritten = unidecode(cat_to_modify['category']['name']['language']['value'].lower().replace(' ', '-'))
        cat_to_modify['category']['link_rewrite']['language']['value'] = link_rewritten

        cat_to_modify['category'].pop('level_depth')
        cat_to_modify['category'].pop('nb_products_recursive')

        prestashop.edit('categories', cat_to_modify)

    '''
    # IT WORKS, BUT PRODUCTS FROM THOSE CATEGORIES ARE DELETED

    remove_change = [r for r in changes if r['ChangeType'] in ['OrderRemove', 'Remove']]
    sorted_remove_change = sorted(remove_change, key=lambda x: x['ID'], reverse=True)

    for cat in sorted_remove_change:
        prestashop.delete('categories', cat['ID'])

    '''

    add_change = [a for a in changes if a['ChangeType'] == 'Add']

    for cat in add_change:
        link_rewritten = unidecode(cat['NameNew'].lower().replace(' ', '-'))

        cat_data = prestashop.get('categories', options={'schema': 'blank'})
        cat_data['category'].update({'id_parent': cat['ParentNew'],
                                     'active': '1',
                                     'name': {'language': {'attrs': {'id': '2'}, 'value': cat['NameNew']}},
                                     'link_rewrite': {'language': {'attrs': {'id': '2'}, 'value': link_rewritten}}
                                     })

        cat_data['category'].pop('id')

        # prestashop.add('categories', cat_data)

    # prestashop.delete('categories', list(range(65, 76)))
