import os
import json
import csv
import requests
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode
import xml.etree.ElementTree as ET

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


def update_products_dict(mode='all', max_products=1000, data_brands_list=None, data_ids_list=None):
    """
    The function updates json file with all products' data with the up-to-date information from the site.
    It selects ids to be updated based on mode and provided data. The default mode updates all products.
    :param data_ids_list: list
            a list of product ids to be updated - works only with mode 'ids'
    :param data_brands_list: list
            a list of product brands to be updated - works only with mode 'brands'
    :param mode: str
            'new'   - updates the file only with new products that are on the website, but not in json file
            'all'   - resets the whole json file and updates all products on the website (DEFAULT)
            'brands'- updates the file only with products of a certain brand
            'ids'   - updates the file only with the specified products' data (serves improve_products function)
    :param max_products:
            serves for testing and limiting the max products edited per use
    :return: confirmation message

    examples of use:
    update_products_dict(mode='new')
    update_products_dict(mode='all')
    update_products_dict(mode='ids', data_ids_list=[23, 231, 53, 132])
    update_products_dict(mode='brands', data_brands_list=['Prokos', 'Retix C'])
    """

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    with open('data/all_products.json', encoding='utf-8') as file:
        product_list = json.load(file)

    indexes_site = prestashop.search('products')
    indexes_dict = [int(p['id']) for p in product_list]

    # default mode is all - it would update all products
    indexes_selected = prestashop.search('products')

    if mode == 'new':
        indexes_new = [index for index in indexes_site if index not in indexes_dict]
        indexes_selected = indexes_new[:max_products]

    if mode == 'ids':
        indexes_selected = data_ids_list[:max_products]

    if mode == 'brands':
        indexes_selected = [int(p['id']) for p in product_list if p['manufacturer_name']['value'] in data_brands_list]

    print(f'Manipulated indexes for all_products.json: {indexes_selected}')

    if len(indexes_selected) > 0:
        product_data = [p for p in product_list if int(p['id']) not in indexes_selected]
        modified_products = [prestashop.get('products', y)['product'] for y in indexes_selected]
        product_data.extend(modified_products)

        print(f'Added/Modified {len(indexes_selected)} products. Total number of products now: {len(product_data)}')
        with open('data/all_products.json', 'w', encoding='utf-8') as file:
            json.dump(product_data, file, indent=4, ensure_ascii=False)
    else:
        print(f'There were no more new products to add. Total number of products now is {len(product_list)}')

    print('FINISHED UPDATING PRODUCTS DICT')


def update_brands_dict():
    with open('data/all_products.json', encoding='utf-8') as file:
        data = json.load(file)

    brands = list(
        set([product['manufacturer_name']['value'] for product in data if product['manufacturer_name']['value']]))
    skus = list(set([product['reference'] for product in data]))
    eans = list(set([product['ean13'] for product in data if len(product['ean13']) > 5]))
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

    brands_dict = {'brand_id': brand_ids, 'brands': brands, 'skus': skus, 'eans': eans, 'indexes': indexes,
                   'brand_sku': skus_list, 'brand_index': indexes_list}

    with open('data/brands_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(brands_dict, file, indent=4, ensure_ascii=False)

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


def get_xml_from_web(source='luminosa'):

    with open(f'data/xml_urls.json', encoding='utf-8') as file:
        url = json.load(file)[source]
    response = requests.get(url)
    if response.status_code == 200:
        xml_content = response.content
        root = ET.fromstring(xml_content)

        if source != 'luminosa':
            attrs_elements = root.findall('.//attrs/a[@name="Kod producenta"]')
            for elem in attrs_elements:
                elem.attrib['name'] = 'Kod_producenta'

            for product in root.findall('o'):
                # print(product.find('desc').text.lower())
                product_sku_element = product.find("attrs/a[@name='Kod_producenta']")
                if product_sku_element is None:
                    missing_sku_element = ET.SubElement(product.find("attrs"), "a", attrib={"name": "Kod_producenta"})
                    missing_sku_element.text = "MISSING"
                product_ean_element = product.find("attrs/a[@name='EAN']")
                if product_ean_element is None:
                    missing_ean_element = ET.SubElement(product.find("attrs"), "a", attrib={"name": "EAN"})
                    missing_ean_element.text = "MISSING"

            xml_content = ET.tostring(root, encoding='utf-8')

        with open(f'data/xml/{source}_feed.xml', 'wb') as file:
            file.write(xml_content)
        print(f"{source.capitalize()} XML fetched successfully!")

    else:
        print("Failed to fetch the XML file!")


def update_everything(site='urodama', product_ids=None):

    print('\nUPDATING DICTIONARIES & XMLs\n')
    if product_ids:
        mode = 'ids'
    else:
        mode = 'all'

    with open(f'data/xml_urls.json', encoding='utf-8') as file:
        url_list = json.load(file)[f'{site}_php_update']
    for url in url_list:
        response = requests.get(url)
        if response.status_code == 200:
            print('Ceneo/Google XML Online updated')

    for xml_site in ['aleja', 'urodama', 'urodama_inci', 'luminosa']:
        get_xml_from_web(source=xml_site)

    update_products_dict(mode=mode, max_products=1000, data_ids_list=product_ids)
    update_brands_dict()
    update_cats_dict(update_cats_to_classify=0)
