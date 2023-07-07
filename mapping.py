import os
import json
import csv
import requests
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


def update_products_json(max_products=10, brand_update=None):
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

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

    print('FINISHED UPDATING ALL PRODUCTS JSON')


def update_brands_dict():
    with open('data/all_products.json', encoding='utf-8') as file:
        data = json.load(file)

    brands = list(
        set([product['manufacturer_name']['value'] for product in data if product['manufacturer_name']['value']]))
    skus = list(set([product['reference'] for product in data]))
    indexes = list(set([product['id'] for product in data]))

    skus_list = {}
    indexes_list = {}

    for b in brands:
        unique_sku = [product['reference'] for product in data if product['manufacturer_name']['value'] == b]
        unique_index = [product['id'] for product in data if product['manufacturer_name']['value'] == b]
        skus_list[b] = unique_sku
        indexes_list[b] = unique_index

    seen_brands = set()
    brand_ids = {}

    for product in data:
        brand = product['manufacturer_name']['value']
        if brand and brand not in seen_brands:
            brand_ids[brand] = product['id_manufacturer']
            seen_brands.add(brand)

    brands_dict = {'brands': brands, 'skus': skus, 'indexes': indexes, 'brand_sku': skus_list,
                   'brand_index': indexes_list, 'brand_id': brand_ids}

    with open('data/brands_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(brands_dict, file)

    print('UPDATED BRANDS DICT')


def update_cats_dict(update_cats_to_classify=0):
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    with open('data/cats_dict.json', encoding='utf-8') as file:
        full_dict = json.load(file)

    # This is basic, workable functionality that ads simple cats_name_id into a cats_dict for classification purposes
    all_cats_ids = prestashop.search('categories')
    cats_list = [prestashop.get('categories', cat_id)['category'] for cat_id in all_cats_ids]
    cats_dict = {cat['name']['language']['value']: cat['id'] for cat in cats_list}
    # print(cats_dict)
    full_dict['cats_name_id'] = cats_dict

    # Updates categories to classify dict in a right format for classification prompts for chatgpt
    if update_cats_to_classify:
        mains = ['Pielęgnacja twarzy', 'Pielęgnacja ciała', 'Kosmetyki do włosów']
        randoms = ['Zestawy kosmetyków', 'NA LATO']

        face_all_id = [category['id'] for category in
                       prestashop.get('categories', 12)['category']['associations']['categories']['category']]
        face_all_list = [prestashop.get('categories', cat_id)['category']['name']['language']['value']
                         for cat_id in face_all_id]
        face_action = [cat for cat in face_all_list if cat.startswith('Kosmetyki')]
        face_form = [cat for cat in face_all_list if not cat.startswith('Kosmetyki')]

        body_all_id = [category['id'] for category in
                       prestashop.get('categories', 14)['category']['associations']['categories']['category']]
        body = [prestashop.get('categories', cat_id)['category']['name']['language']['value']
                for cat_id in body_all_id]
        hair_all_id = [category['id'] for category in
                       prestashop.get('categories', 31)['category']['associations']['categories']['category']]
        hair = [prestashop.get('categories', cat_id)['category']['name']['language']['value']
                for cat_id in hair_all_id]

        full_dict['cats_classify'] = {'cat_main': mains, 'cat_random': randoms, 'cat_face_form': face_form,
                                      'cat_face_action': face_action, 'cat_body': body, 'cat_hair': hair}

    with open('data/cats_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(full_dict, file, indent=4, ensure_ascii=False)

    print('UPDATED CATS DICT')


# update_cats_dict(update_cats_to_classify=0)


# FUNCTIONS BELOW ARE SUPPOSED TO BE USED ONLY ONE WHILE SETTING UP THE ENVIRONMENT AFTER MIGRATION


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

    reassign_categories_setter(initial_mode=1)

    remove_change = [r for r in changes if r['ChangeType'] in ['OrderRemove', 'Remove']]
    sorted_remove_change = sorted(remove_change, key=lambda x: x['ID'], reverse=True)

    for cat in sorted_remove_change:
        prestashop.delete('categories', cat['ID'])

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

        prestashop.add('categories', cat_data)

    # prestashop.delete('categories', list(range(65, 76)))


def reassign_categories_setter(initial_mode=1, cats_to_reassign=None, cats_substitutes=None):
    with open('data/all_products.json', encoding='utf-8') as file:
        data = json.load(file)

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    if initial_mode == 1:
        # initial values from the first setting up of the categories tree
        cats_to_reassign = [20, 21, 22, 23, 27, 35, 37, 39, 40]
        cats_substitutes = [13, 13, 13, 13, 14, 44, 47, 38, 38]

    cats_mapped = list(zip(cats_to_reassign, cats_substitutes))

    for cat in cats_mapped:
        products_cat_x = [p for p in data if p['id_category_default'] == str(cat[0])]
        # print(f'Category {cat[0]} is main category in {len(products_cat_X)} instances')

        for x in products_cat_x:
            x['id_category_default'] = str(cat[1])

            product_edit = prestashop.get('products', x['id'])

            product_edit['product']['id_category_default'] = x['id_category_default']

            product_edit['product'].pop('manufacturer_name')
            product_edit['product'].pop('quantity')

            product_edit['product']['position_in_category']['value'] = str(1)

            # print(product_edit)

            prestashop.edit('products', product_edit)


def get_xml_from_web(source='luminosa'):
    with open(f'data/xml_urls.json') as file:
        url = json.load(file)[source]
    response = requests.get(url)
    if response.status_code == 200:
        with open(f'data/{source}_feed.xml', 'wb') as file:
            file.write(response.content)
        print("File saved successfully!")
    else:
        print("Failed to fetch the XML file!")
