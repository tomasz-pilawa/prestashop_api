import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET
import openai
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re

import ai_boosting
import mapping

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')
openai.api_key = os.getenv('openai_api')

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


def extract_plain_text(html_content):
    """
    Used for simple processing to remove html tags from meta.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()


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
        lists = json.load(file)
    sku_list = lists['skus']
    ean_list = lists['eans']

    for product in selected_products:
        product_sku = product.find("attrs/a[@name='Kod_producenta']").text.strip()
        if product_sku in sku_list:
            selected_products.remove(product)
    for product in selected_products:
        product_ean = product.find("attrs/a[@name='EAN']").text.strip()
        if product_ean in ean_list:
            selected_products.remove(product)

    if mode == 'brands':
        products_temp = [product for product in selected_products
                         if product.find("attrs/a[@name='Producent']").text.strip() in data]
        selected_products = products_temp

    elif mode == 'exclude':
        products_temp = [product for product in selected_products if int(product.get('id')) not in data]
        selected_products = products_temp

    elif mode == 'include':
        products_temp = [product for product in selected_products if int(product.get('id')) in data]
        selected_products = products_temp

    if print_info:
        print(f'\nThere are potentially {len(selected_products)} products to add from the XML file\n')
        print('PRODUCT NAME, SHOP ID, SKU, EAN, PRICE, LINK')
        for p in selected_products:
            sku = p.find("attrs/a[@name='Kod_producenta']").text.strip()
            ean = p.find("attrs/a[@name='EAN']").text.strip()

            print(f"{p.find('name').text.strip()},{p.get('id')},{sku},{ean},{p.get('price')},{p.get('url').strip()}")

        selected_ids = [int(p.get('id')) for p in selected_products]
        print(selected_ids)

    return selected_products


# select_products_xml(source='luminosa', mode='brands', data=['Germaine de Capuccini', 'Mesoestetic'], print_info=1)
# select_products_xml(source='ampari', mode='brands', data=['Helen Seward'], print_info=1)


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

        data['reference'] = single_product.find("attrs/a[@name='Kod_producenta']").text.strip('\n ')

        ean_raw = single_product.find("attrs/a[@name='EAN']").text
        data['ean13'] = ''.join([char for char in ean_raw if char.isdigit()])

        data['price'] = single_product.get('price')
        data['wholesale_price'] = str(round(float(data['price']) / price_ratio, 2))
        data['name'] = single_product.find('name').text.strip('\n ')

        if single_product.find("attrs/a[@name='Producent']").text in list(manufacturer_dict.keys()):
            data['id_manufacturer'] = manufacturer_dict[single_product.find("attrs/a[@name='Producent']").text]
        else:
            data.pop('id_manufacturer', None)

        data['id_category_default'] = 2
        data['link_rewrite'] = data['name'].lower().replace(' ', '-')

        data['description'] = single_product.find('desc').text.split('div class')[0]
        data['description_short'] = single_product.find('desc').text.split('</p><p>')[0]
        data['meta_title'] = truncate_string(data['name'], 70).strip('\n ')
        data['meta_description'] = truncate_string(extract_plain_text(single_product.find('desc').text), 160).strip('\n ')

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
        image_response = requests.get(image_url)

        if image_response.status_code == 200:
            filename = f"{single_product['link_rewrite']['language']['value']}-kosmetyki-urodama.jpg"
            image_path = "images/" + filename

            with open(image_path, "wb") as file:
                file.write(image_response.content)

            with open(image_path, "rb") as file:
                image_content = file.read()

            prestashop.add(f'/images/products/{product_id}', files=[('image', filename, image_content)])

            write_to_csv(file_path='data/logs/added_products_raw.csv', product_dict=single_product)

        else:
            print(f"Failed to download image for product: {single_product['name']['language']['value']}")
            continue

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
        if not product['product']['position_in_category']['value'].isdigit():
            product['product']['position_in_category']['value'] = '1'
        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        fixed_ids.append(int(r['ID_u']))

        print(product)
        prestashop.edit('products', product)

        # writes a log of all changes in nice format
        product_log.update({
            'ID_urodama': product['product']['id'],
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


def add_product_from_xml(select_source=None, select_mode=None, select_data=None, process_max_products=2):
    products = select_products_xml(source=select_source, mode=select_mode, data=select_data)
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

    mapping.update_products_dict(mode='ids', data_ids_list=product_ids)
    mapping.update_brands_dict()
    mapping.update_cats_dict(update_cats_to_classify=0)


# improve_products(file_path_fix='data/logs/__dummy_testing_change.csv', classify_ai=1)

# add_product_from_xml(select_source='luminosa', process_max_products=2)
# prestashop.delete('products', [792, 793])


def check_inci(limit=5, file=None):

    tree = ET.parse(f'data/{file}')
    root = tree.getroot()
    all_products = root.findall('o')

    ids_no_inci = []
    brands = ["Filorga", "Mesoestetic", "Anna Lotan", "Sesderma", "LEIM", "Germaine de Capuccini", "Fusion Mesotherapy",
              "Prokos", "Retix C", "Exuviance", "GUAM Lacote", "Lidooxin", "Magnipsor", "Colway", "Croma Pharma",
              "Montibello", "Footlogix"]
    brand_counts = {brand: 0 for brand in brands}

    for p in all_products[:limit]:
        p_name = p.find('name').text
        p_id = int(p.get('id'))
        p_desc = p.find('desc').text.lower()

        if 'inci' in p_desc:
            x = p_desc.split('inci')[1]

            soup = BeautifulSoup(x, 'html.parser')
            inci_p = soup.find('p', string=True)
            # print(inci_p.get_text())

        else:
            ids_no_inci.append(p_id)
            print(p_name.strip())
            for brand in brands:
                if p.find(".//attrs/a[@name='Producent']").text.strip().lower() == brand.lower():
                    brand_counts[brand] += 1

    print(f"There are {len(ids_no_inci)} products (out of {len(all_products[:limit])}) without valid INCI code. "
          f"Here's the list of them")
    print(ids_no_inci)
    print(brand_counts)


def fill_brand_inci(brand='Mesoestetic', limit=2, source='luminosa'):

    # Get list of brand IDs from json dict
    with open('data/brands_dict.json', encoding='utf-8') as file:
        all_brand_ids = json.load(file)['brand_index'][brand]

    # Load source products' data in xml tree
    tree = ET.parse(f'data/{source}_feed.xml')
    root = tree.getroot()
    source_products = root.findall('o')

    # Iterate over all Products and fill in Inci if either SKU or EAN matches any product in source database
    for p_id in all_brand_ids[:limit]:
        product = prestashop.get('products', p_id)['product']
        print(f"\nCHECKING PRODUCT {product['name']['language']['value']}")

        # Check if there is no INCI at the moment
        if 'inci' not in product['description']['language']['value'].lower():
            print('There is no INCI on the website. Proceeding with the loop.')
            sku = product['reference']
            ean = product['ean13']
            product_found = False
            s_inci = None

            # Firstly, find the any matching sku/ean
            for s in source_products:
                s_sku = s.find("attrs/a[@name='Kod_producenta']").text.strip()
                s_ean = s.find("attrs/a[@name='EAN']").text.strip()

                # Secondly, if there is a match, print names & check for INCI
                if sku == s_sku or ean == s_ean:
                    print(sku, s_sku)
                    print(ean, s_ean)
                    # print(product['name']['language']['value'])
                    print(s.find('name').text.strip())

                    product_found = True
                    s_desc = s.find('desc').text.lower()

                    # Thirdly, if there is INCI in the source - insert it via API directly and break the loop
                    if 'inci' in s_desc:
                        soup = BeautifulSoup(s_desc.split('inci')[1], 'html.parser')
                        s_inci = soup.find('p', string=True).get_text()

                        s_inci = '<p><strong>Skład INCI</strong></p><p>' + s_inci + '</p>'
                        product['description']['language']['value'] += s_inci

                        product.pop('manufacturer_name')
                        product.pop('quantity')
                        if int(product['position_in_category']['value']) < 1:
                            product['position_in_category']['value'] = str(1)
                        prestashop.edit('products', {'product': product})
                        print('Inserted INCI')
                        break

                    else:
                        print('There is no INCI in the source description')

            if not product_found:
                print(f"{product['name']['language']['value']} doesn't exist in source database")

        else:
            print('The INCI is already there')

    response = requests.get('https://urodama.pl/ceneoinci.php')
    if response.status_code == 200:
        print('\nCeneo PHP updated')
    mapping.get_xml_from_web(source='urodama_inci')

    print('\nFINISHED THE SCRIPT')


# mapping.get_xml_from_web(source='urodama')
# check_inci(limit=500, file='urodama_inci_feed.xml')
# fill_brand_inci(limit=100, brand='Footlogix', source='luminosa')


def set_unit_price(limit=400, site='urodama'):

    tree = ET.parse(f'data/{site}_feed.xml')
    root = tree.getroot()
    source_products = root.findall('o')
    indexes = [int(p.get('id')) for p in source_products]

    for i in indexes[:limit]:
        product = prestashop.get('products', i)['product']

        name = product['name']['language']['value']
        print(name)
        quantity = None

        matches = re.findall(r'(\d+)\s*ml', name)
        if matches:
            quantity = sum([int(match) for match in matches])

        m2 = re.search(r'(\d+)\s*x\s*(\d+)', name)
        if m2:
            num1 = int(m2.group(1))
            num2 = int(m2.group(2))
            quantity = num1 * num2

        if re.search(r'\d+\s*g|\s*g', name):
            quantity = None
        if 'Zestaw Xylogic' in name:
            quantity = None
        if 'kg' in name:
            quantity = None


        print(quantity)

        # print(product['unity'])
        # print(product['unit_price_ratio'])


# set_unit_price()
