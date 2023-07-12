import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET
import openai
import requests
from datetime import datetime

import ai_boosting

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')

# openai.api_key = os.getenv('openai_api')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


def truncate_string(text, max_length=70):
    """
    Truncates the string to 70 characters max. Necessary due to limits on Prestashop Meta Title variable.
    """
    if len(text) > max_length:
        truncated_text = text[:max_length - 3] + "..."
    else:
        truncated_text = text
    return truncated_text


def select_products_xml(source='luminosa', mode=None, data=None, print_info=None):
    """
    EXAMPLES OF USAGE OF THIS FUNCTION
    select_products_xml(source='luminosa', mode='brands', data=['Essente', 'Mesoestetic'], print_info=1)
    select_products_xml(source='luminosa', mode='brands', data=['Mesoestetic'], print_info=1)
    select_products_xml(source='luminosa', mode='exclude', data=[716, 31, 711, 535, 723, 55], print_info=1)
    select_products_xml(source='luminosa', mode='include', data=[716, 31, 711, 535, 723, 55], print_info=1)
    """

    tree = ET.parse(f'data/{source}_feed.xml')
    root = tree.getroot()

    selected_products = root.findall('o')

    with open('data/brands_dict.json', encoding='utf-8') as file:
        sku_list = json.load(file)['skus']

    for product in selected_products:
        product_sku = product.find("attrs/a[@name='Kod_producenta']").text
        if product_sku in sku_list:
            selected_products.remove(product)

    if mode == 'brands':
        products_temp = [product for product in selected_products
                         if product.find("attrs/a[@name='Producent']").text in data]
        selected_products = products_temp

    elif mode == 'exclude':
        products_temp = [product for product in selected_products if int(product.get('id')) not in data]
        selected_products = products_temp

    elif mode == 'include':
        products_temp = [product for product in selected_products if int(product.get('id')) in data]
        selected_products = products_temp

    if print_info:
        print(f'\nThere are potentially {len(selected_products)} products to add from the XML file\n')
        for p in selected_products:
            print(p.find('name').text)
            print(p.get('id'))
            print(p.find("attrs/a[@name='Kod_producenta']").text)

        selected_ids = [int(p.get('id')) for p in selected_products]
        print(selected_ids)

    return selected_products


def process_products(product_list, max_products=5):
    """
    The function takes list of products in XML tree format and converts it to simpler python list of dictionaries
    with only necessary attributes that are needed for adding a new product via Prestashop API.
    :param product_list: XML tree
            List of products in XML tree format that would be processed and converted to simpler list of dictionaries
    :param max_products: integer
            Limits the number of products to be processed. Used mostly during development
    :return: processed_products: list of dictionaries
            All necessary data for the products to be added to Prestashop. Should be passed to add_with_photo function
    """

    default_data = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404", "condition": "new",
                    "show_price": "1", "indexed": "1", "visibility": "both"}

    with open('data/brands_dict.json', encoding='utf-8') as file:
        manufacturer_dict = json.load(file)['brand_id']

    price_ratio = 1.87

    processed_products = []

    for single_product in product_list[:max_products]:
        data = dict(default_data)

        data['reference'] = single_product.find("attrs/a[@name='Kod_producenta']").text
        data['ean13'] = single_product.find("attrs/a[@name='EAN']").text
        data['price'] = single_product.get('price')
        data['wholesale_price'] = str(round(float(data['price']) / price_ratio, 2))
        data['name'] = single_product.find('name').text

        if single_product.find("attrs/a[@name='Producent']").text in list(manufacturer_dict.keys()):
            data['id_manufacturer'] = manufacturer_dict[single_product.find("attrs/a[@name='Producent']").text]
        else:
            data.pop('id_manufacturer', None)

        data['id_category_default'] = 2
        data['link_rewrite'] = data['name'].lower().replace(' ', '-')

        data['description'] = single_product.find('desc').text.split('div class')[0]
        data['description_short'] = single_product.find('desc').text.split('</p><p>')[0]
        data['meta_title'] = truncate_string(data['name'], 70)
        data['meta_description'] = truncate_string(data['description'][3:].split('.')[0] + '.', 160)

        data['image_url'] = single_product.find("imgs/main").get('url')

        # print(data)
        processed_products.append(data)

    return processed_products


def add_with_photo(product_list):

    indexes_added = []

    for single_product in product_list:

        for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
            single_product[x] = {'language': {'attrs': {'id': '2'}, 'value': single_product[x]}}

        # this prevents mutability to occur (passing by reference as they are the same object in memory)
        product_info = {'product': dict(single_product)}
        product_info['product'].pop('image_url')

        print(single_product)

        response = prestashop.add('products', product_info)
        product_id = int(response['prestashop']['product']['id'])
        indexes_added.append(product_id)
        single_product['product_id'] = product_id

        image_url = single_product['image_url']
        response = requests.get(image_url)
        response.raise_for_status()

        filename = f"{single_product['link_rewrite']['language']['value']}-kosmetyki-urodama.jpg"
        image_path = "images/" + filename

        with open(image_path, "wb") as file:
            file.write(response.content)

        with open(image_path, "rb") as file:
            image_content = file.read()

        prestashop.add(f'/images/products/{product_id}', files=[('image', filename, image_content)])

        write_to_csv(file_path='data/logs/added_products_raw.csv', product_dict=single_product)

    print('SUCCESS!!! Indexes added:')
    print(indexes_added)

    return indexes_added


def write_to_csv(file_path, product_dict):

    row_data = {
        'ID_u': product_dict['product_id'],
        'ref': product_dict['reference'],
        'nazwa': product_dict['name']['language']['value'],
        'active': product_dict['state'],
        'brand': '',
        'wprowadzony': datetime.now().strftime("%d-%m-%Y %H:%M"),
        'Comments': product_dict['ean13'],
        'Sales 2021': 0,
        'Sales 2022': 0,
        'COST NET': product_dict['wholesale_price'],
        'PRICE': product_dict['price']
    }

    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=row_data.keys())
        writer.writerow(row_data)


def fix_data_from_csv(file_path):

    fixed_ids = []
    products_log_list = []

    with open(file_path, encoding='utf-8', newline='') as file:
        reader = list(csv.DictReader(file))

    for r in reader:
        product = prestashop.get('products', r['ID_u'])

        # writes initial data into the log
        product_log = dict(SKU_old=product['product']['reference'],
                           EAN_old=product['product']['ean13'],
                           active_old=product['product']['state'],
                           name_old=product['product']['name']['language']['value'],
                           cost_old=product['product']['wholesale_price'],
                           price_old=product['product']['price'])

        product['product']['reference'] = r['ref']
        product['product']['name']['language']['value'] = r['nazwa']
        product['product']['ean13'] = r['Comments']

        product['product']['price'] = r['PRICE'].strip().replace(',', '.')
        product['product']['wholesale_price'] = r['COST NET'].strip().replace(',', '.')

        with open('data/brands_dict.json', encoding='utf-8') as file:
            manufacturer_dict = json.load(file)['brand_id']

        product['product']['id_manufacturer'] = manufacturer_dict[r['brand']]

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')
        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        fixed_ids.append(int(r['ID_u']))

        print(product)
        prestashop.edit('products', product)

        # writes a log of all changes in nice format
        product_log.update({
            'ID_urodama': product['product']['product_id'],
            'date_change': datetime.now().strftime("%d-%m-%Y %H:%M"),
            'brand_id': product['product']['id_manufacturer'],
            'SKU_new': product['product']['reference'],
            'EAN_new': product['product']['ean13'],
            'active_new': product['product']['state'],
            'name_new': product['product']['name']['language']['value'],
            'cost_new': product['product']['wholesale_price'],
            'price_new': product['product']['price']
        })
        products_log_list.append(product_log)

    print('FINISHED FIXING FROM CSV')

    return fixed_ids, products_log_list


def add_product_from_xml(select_source=None, select_mode=None, select_ids=None, process_max_products=2):
    products = select_products_xml(source=select_source, mode=select_mode, data=select_ids)
    products = process_products(products, max_products=process_max_products)
    add_with_photo(products)


def improve_products(file_path_fix=None, classify_ai=0, descriptions_ai=0, features_ai=0):

    product_ids, product_logs = fix_data_from_csv(file_path=file_path_fix)

    if classify_ai:
        ai_boosting.classify_categories(product_ids)
    if descriptions_ai:
        ai_boosting.write_descriptions(product_ids)
    if features_ai:
        # ai_boosting.configure_features(products_ids)
        pass

    # writes log for all changes
    for product in product_logs:
        product.update({'classify_ai': classify_ai, 'descriptions_ai': descriptions_ai, 'features_ai': features_ai})
        with open('data/logs/improved_products_log.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=product.keys())
            writer.writerow(product)

    # update_dicts()


# improve_products(file_path_fix='data/logs/__dummy_testing_change.csv', classify_ai=1)

# add_product_from_xml(select_source='luminosa', process_max_products=2)
# prestashop.delete('products', [786, 787])
