import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import pymysql
import logging

import mapping

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


def select_products_xml(source='luminosa', mode=None, data=None, print_info=None):

    tree = ET.parse(f'data/xml/{source}_feed.xml')
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
        data['description_short'] = BeautifulSoup(single_product.find('desc').text, 'html.parser').\
            get_text()[:600].strip('\n')
        data['meta_title'] = data['name'].strip('\n ')
        data['meta_description'] = BeautifulSoup(single_product.find('desc').text, 'html.parser').\
            get_text()[:200].strip('\n')

        data['image_url'] = single_product.find("imgs/main").get('url')

        # print(data)
        processed_products.append(data)

    return processed_products


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


def add_with_photo(product_list):

    indexes_added = []

    for single_product in product_list:

        # for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
        #     single_product[x] = {'language': {'attrs': {'id': '2'}, 'value': single_product[x]}}

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


def fix_products(source=None):

    if type(source) == str:

        fixed_ids = []
        with open(f'data/logs/{source}.csv', encoding='utf-8', newline='') as file:
            reader = list(csv.DictReader(file))

        for r in reader:
            product = prestashop.get('products', r['ID_u'])['product']
            product['reference'] = r['ref']
            product['name']['language']['value'] = r['nazwa']
            product['ean13'] = r['Comments']

            product['price'] = r['PRICE'].strip().replace(',', '.')
            product['wholesale_price'] = r['COST NET'].strip().replace(',', '.')

            with open('data/brands_dict.json', encoding='utf-8') as file:
                manufacturer_dict = json.load(file)['brand_id']

            product['id_manufacturer'] = manufacturer_dict[r['brand']]

            fixed_ids.append(int(r['ID_u']))

            print(product)
            edit_presta_product(product=product)
    else:
        fixed_ids = source

    print('FINISHED FIXING THE PRODUCTS (CSV, INCI, UNIT PRICE)\n')

    return fixed_ids


def fill_inci(brand=None, limit=2, source='aleja_inci', product_ids=None):

    # Get list of brand IDs from json dict or set ids to be fixed or return early
    if brand:
        with open('data/brands_dict.json', encoding='utf-8') as file:
            ids_to_fix = json.load(file)['brand_index'][brand]
    elif product_ids:
        ids_to_fix = product_ids
    else:
        print('No brand or product ids given hence no INCI inserted')
        return

    # Load source products' data in xml tree
    tree = ET.parse(f'data/xml/{source}_feed.xml')
    root = tree.getroot()
    source_products = root.findall('o')

    # Iterate over all Products and fill in INCI if either SKU or EAN matches any product in source database
    for p_id in ids_to_fix[:limit]:
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
                        # s_inci = soup.find('p', string=True).get_text()
                        s_inci = soup.find('p', string=True)
                        if s_inci:
                            s_inci_text = s_inci.get_text()
                        else:
                            s_inci_text = soup.get_text()

                        s_inci = '<p></p><p><strong>Skład INCI:</strong></p><p>' + s_inci_text + '</p>'
                        product['description']['language']['value'] += s_inci

                        edit_presta_product(product=product)
                        break

                    else:
                        print('There is no INCI in the source description')

            if not product_found:
                print(f"{product['name']['language']['value']} doesn't exist in source database")

        else:
            print('The INCI is already there')

    print('FINISHED INSERTING INCI\n')


def set_unit_price_api_sql(site='urodama', product_ids=None, limit=5):

    # Connect to Prestashop API to get the data for unit price manipulation
    api_url = os.getenv(f'{site}_link')
    api_key = os.getenv(f'{site}_pass')
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    # switch enabling manipulating only specified product ids
    if not product_ids:
        indexes = prestashop.search('products')
    else:
        indexes = product_ids

    # Get SQL connection passes
    with open('data/php_access.json', encoding='utf-8') as file:
        php_access = json.load(file)[site]
    pass_php = os.getenv(f'pass_php_{site}')

    # Connect to the database
    conn = pymysql.connect(
        host=php_access['host'],
        port=3306,
        user=php_access['user'],
        password=pass_php,
        db=php_access['db'])

    try:
        c = conn.cursor()
        conn.begin()

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
            if 'kg' in name:
                quantity = None

            if quantity is not None:
                c.execute(php_access['query'], (quantity, product['id']))

        conn.commit()

    except Exception as e:
        print("Error:", e)
        conn.rollback()
    finally:
        c.close()
        conn.close()


def manipulate_desc(desc):

    summary, ingredients = '', ''

    cleaned_text = re.sub(r'\n+(?![^\n]*:)', ' ', desc)
    cleaned_text = re.sub(r'&#\d+;', '', cleaned_text).replace('&nbsp;', '').replace('</b>', '').replace('<b>', '').\
        replace(' •', '')

    inci_split = re.split(r'skład inci', cleaned_text, flags=re.IGNORECASE)
    if len(inci_split) >= 2:
        cleaned_text = inci_split[0].strip()

    active_split = re.split(r'składniki aktywne:', cleaned_text, flags=re.IGNORECASE)

    if len(active_split) >= 2:
        summary = active_split[0].strip()
        ingredients = active_split[1].strip()
    else:
        summary = cleaned_text
        ingredients = cleaned_text

    return summary[:3000], ingredients[:3000]


def make_desc(desc):

    desc_short = desc.split('SHORT DESCRIPTION:')[1].strip()
    desc_long = desc.split('SHORT DESCRIPTION:')[0].replace('LONG DESCRIPTION:', '').strip().\
        replace('Właściwości i Zalety kosmetyku:', '</p><p><strong>Właściwości i Zalety kosmetyku:</strong>')

    desc_short = re.sub(r'\n& ', r'</li><li>', desc_short)
    desc_short = re.sub(r'& ', r'<li>', desc_short)
    desc_short = f'<ul style="list-style-type: disc;">{desc_short}</li></ul>'

    desc_long = re.sub(r'\n& ', r'</li><li>', desc_long)
    desc_long = re.sub(r'\n\n', '</p><p>', desc_long)
    desc_long = desc_long.replace('</strong></li><li>', '</strong></p><ul style="list-style-type: disc;"><li>')
    desc_long = f'<p>{desc_long}</li></ul>'

    return desc_short, desc_long


def make_active(desc):

    desc = re.sub(r'SKŁADNIKI:',
                  r'<p></p><p><strong>Składniki aktywne:</strong></p><ul style="list-style-type: disc;">', desc)
    desc = re.sub(r'(\n&|\n-)', r'</li><li>', desc).replace('</li>', '', 1)
    desc = re.sub(r'\n\nSPOSÓB UŻYCIA:', r'</li></ul><p></p><p><strong>Sposób użycia:</strong><p>', desc + '</p>')

    return desc


def edit_presta_product(product):

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    product.pop('manufacturer_name')
    product.pop('quantity')
    product.pop('position_in_category')

    prestashop.edit('products', {'product': product})

    print(f"Edited product {product['name']['language']['value']}")


def truncate_meta(text, max_length=160):

    sentences = text.split('. ')
    output = sentences[0] + '. '

    remaining_length = max_length - len(output)
    remaining_sentences = sorted(sentences[1:], key=len, reverse=True)

    for sentence in remaining_sentences:
        sentence_length = len(sentence) + 2
        if sentence_length <= remaining_length:
            output += sentence
            remaining_length -= sentence_length
        else:
            break

    return output.strip()


def explore_brand(brand, source='aleja'):

    product_tree = ET.parse(f'data/xml/{source}_feed.xml')
    all_products = product_tree.getroot().findall('o')

    with open('data/brands_dict.json', encoding='utf-8') as file:
        excluded_products_list = json.load(file)
    excluded_sku = excluded_products_list.get('skus', [])
    excluded_ean = excluded_products_list.get('eans', [])

    selected_products = [product for product in all_products if
                         product.find("attrs/a[@name='Producent']").text.strip() in brand and
                         product.find("attrs/a[@name='Kod_producenta']").text.strip() not in excluded_sku and
                         product.find("attrs/a[@name='EAN']").text.strip() not in excluded_ean]

    for p in selected_products:
        product_data = {
                    'ID_TARGET': '',
                    'SKU': p.find("attrs/a[@name='Kod_producenta']").text.strip(),
                    'Product Name': p.find('name').text.strip(),
                    'Active': 1,
                    'Brand': brand,
                    'Date': datetime.now().strftime("%d-%m-%Y %H:%M"),
                    'EAN': p.find("attrs/a[@name='EAN']").text.strip(),
                    'Sales 2021': 0,
                    'Sales 2022': 0,
                    'COST NET': str(round(float(p.get('price'))/1.87, 2)).replace('.', ','),
                    'PRICE': str(p.get('price')).replace('.', ','),
                    'LINK': p.get('url').strip(),
                    'ID_SOURCE': p.get('id')
        }

        with open('data/logs/_product_ideas.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=product_data.keys())
            writer.writerow(product_data)

    logging.info('Explore_brand: Saved potential product ideas to csv file')


# explore_brand(brand='Montibello')


def process_products_from_csv(source_csv, source_desc_xml='aleja'):

    default_product_data = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404",
                            "condition": "new", "show_price": "1", "indexed": "1", "visibility": "both"}

    with open(f'data/logs/{source_csv}.csv', encoding='utf-8', newline='') as file:
        products_to_add = list(csv.DictReader(file))

    product_tree = ET.parse(f'data/xml/{source_desc_xml}_feed.xml')

    processed_products = []

    for product_source in products_to_add:
        product = dict(default_product_data)

        product['name'] = product_source.get('Product Name', None)
        product['reference'] = product_source.get('SKU', None)
        product['ean13'] = product_source.get('EAN', None)
        product['price'] = product_source.get('PRICE', None).replace(',', '.')
        product['wholesale_price'] = product_source.get('COST NET', None).replace(',', '.')
        product['id_category_default'] = 2
        product['link_rewrite'] = product.get('name', 'NAME NOT FOUND').lower().replace(' ', '-')

        with open('data/brands_dict.json', encoding='utf-8') as f:
            brand_ids_dict = json.load(f).get('brand_id', None)
        brand = product_source.get('Brand', None)
        product['id_manufacturer'] = brand_ids_dict.get(brand, None)

        product_id_xml = product_source.get('ID_SOURCE', None)
        product_xml = product_tree.find(f'.//o[@id="{product_id_xml}"]')

        product['description'] = product_xml.find('desc').text.strip().replace('&#8211;', '-').replace('&nbsp', '')
        product['description_short'] = '.'.join(product['description'].replace('\n', ' ').split('.')[:3]) + '.'[:800]
        product['meta_title'] = product['name']
        product['meta_description'] = truncate_meta(product['description_short'], 160)[:180]
        product['image_url'] = product_xml.find("imgs/main").get('url')

        for text in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
            product[text] = {'language': {'attrs': {'id': '2'}, 'value': product[text]}}

        processed_products.append(product)

    logging.info('Finished processing products from CSV.')
    return processed_products


# source = 'test_adding'
# products = process_products_from_csv(source_csv=source)
# add_with_photo(product_list=products)





