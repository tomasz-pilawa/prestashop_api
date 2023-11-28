import os
import json
import csv
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import pymysql
import logging


def explore_brand(brand: str, source: str = 'aleja'):
    product_tree = ET.parse(f'data/xml/{source}_feed.xml')
    all_products = product_tree.getroot().findall('o')

    with open('../data/brands_dict.json', encoding='utf-8') as file:
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
            'COST NET': str(round(float(p.get('price')) / 1.87, 2)).replace('.', ','),
            'PRICE': str(p.get('price')).replace('.', ','),
            'LINK': p.get('url').strip(),
            'ID_SOURCE': p.get('id')
        }

        with open('../data/logs/_product_ideas.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=product_data.keys())
            writer.writerow(product_data)

    logging.info('Explore_brand: Saved potential product ideas to csv file')


def process_products_from_csv(source_csv: str, source_desc_xml: str = 'aleja') -> list:
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

        with open('../data/brands_dict.json', encoding='utf-8') as f:
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


def add_products_api(prestashop, product_list: list):
    indexes_added = []

    for product in product_list:
        product_upload_data = {'product': dict(product)}
        product_upload_data['product'].pop('image_url')

        response = prestashop.add('products', product_upload_data)
        product_id = int(response['prestashop']['product']['id'])
        indexes_added.append(product_id)

        image_response = requests.get(product.get('image_url', None))
        if image_response.status_code == 200:
            filename = f"{product['link_rewrite']['language']['value']}-kosmetyki-urodama.jpg"
            image_path = "images/" + filename
            with open(image_path, "wb") as file:
                file.write(image_response.content)
            with open(image_path, "rb") as file:
                image_content = file.read()
            prestashop.add(f'/images/products/{product_id}', files=[('image', filename, image_content)])
        else:
            logging.info(f"Failed to download image for product: {product['name']['language']['value']}")
            continue

    with open('../data/logs/product_indexes.json', 'w') as file:
        json.dump(indexes_added, file)
    logging.info(f'Finished adding {len(product_list)} with photos to Prestashop database via API.')


def fill_inci(prestashop, product_ids: list[int], source: str = 'aleja'):

    product_tree = ET.parse(f'data/xml/{source}_feed.xml')
    source_products = product_tree.getroot().findall('o')

    for product_id in product_ids:
        target_product = prestashop.get('products', product_id).get('product')

        if 'inci' not in target_product['description']['language']['value'].lower():
            target_sku = target_product['reference']
            target_ean = target_product['ean13']

            for source_product in source_products:
                source_sku = source_product.find("attrs/a[@name='Kod_producenta']").text.strip()
                source_ean = source_product.find("attrs/a[@name='EAN']").text.strip()

                if target_sku == source_sku or target_ean == source_ean:
                    source_desc = source_product.find('desc').text.lower()

                    if 'inci' in source_desc:
                        soup = BeautifulSoup(source_desc.split('inci')[1], 'html.parser')
                        source_inci = soup.find('p', string=True)
                        source_inci_text = source_inci.get_text() if source_inci else soup.get_text()

                        target_inci = '<p></p><p><strong>Skład INCI:</strong></p><p>' + source_inci_text + '</p>'
                        target_product['description']['language']['value'] += target_inci
                        edit_presta_product(prestashop, product=target_product)
                        break
                    else:
                        logging.info(f"No INCI in the source description for product {target_product.get('name')}")
                        break

    logging.info('FINISHED Inserting INCI into selected products')


def set_unit_price_api_sql(prestashop, product_ids: list[int], site: str = 'urodama'):

    with open('../data/php_access.json', encoding='utf-8') as file:
        php_access = json.load(file)[site]
    pass_php = os.getenv('URODAMA_PHP_KEY')
    conn = pymysql.connect(
        host=php_access['host'],
        port=3306,
        user=php_access['user'],
        password=pass_php,
        db=php_access['db'])

    try:
        c = conn.cursor()
        conn.begin()

        for product_id in product_ids:
            product = prestashop.get('products', product_id)['product']
            product_name = product['name']['language']['value']
            quantity = None

            matches = re.findall(r'(\d+)\s*ml', product_name)
            if matches:
                quantity = sum([int(match) for match in matches])

            matches_2 = re.search(r'(\d+)\s*x\s*(\d+)', product_name)
            if matches_2:
                quantity = int(matches_2.group(1)) * int(matches_2.group(2))

            if 'kg' in product_name:
                quantity = None
            if quantity is not None:
                c.execute(php_access['query'], (quantity, product['id']))
        conn.commit()
    except Exception as e:
        logging.error("Error:", e)
        conn.rollback()
    finally:
        c.close()
        conn.close()


def manipulate_desc(desc: str) -> tuple[str, str]:

    cleaned_text = re.sub(r'\n+(?![^\n]*:)', ' ', desc)
    cleaned_text = re.sub(r'&#\d+;', '', cleaned_text).replace('&nbsp;', '').replace('</b>', '').replace('<b>', ''). \
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


def make_desc(desc: str) -> tuple[str, str]:
    desc_short = desc.split('SHORT DESCRIPTION:')[1].strip()
    desc_long = desc.split('SHORT DESCRIPTION:')[0].replace('LONG DESCRIPTION:', '').strip(). \
        replace('Właściwości i Zalety kosmetyku:', '</p><p><strong>Właściwości i Zalety kosmetyku:</strong>')

    desc_short = re.sub(r'\n& ', r'</li><li>', desc_short)
    desc_short = re.sub(r'& ', r'<li>', desc_short)
    desc_short = f'<ul style="list-style-type: disc;">{desc_short}</li></ul>'

    desc_long = re.sub(r'\n& ', r'</li><li>', desc_long)
    desc_long = re.sub(r'\n\n', '</p><p>', desc_long)
    desc_long = desc_long.replace('</strong></li><li>', '</strong></p><ul style="list-style-type: disc;"><li>')
    desc_long = f'<p>{desc_long}</li></ul>'

    return desc_short, desc_long


def make_active(desc: str) -> str:
    desc = re.sub(r'SKŁADNIKI:',
                  r'<p></p><p><strong>Składniki aktywne:</strong></p><ul style="list-style-type: disc;">', desc)
    desc = re.sub(r'(\n&|\n-)', r'</li><li>', desc).replace('</li>', '', 1)
    desc = re.sub(r'\n\nSPOSÓB UŻYCIA:', r'</li></ul><p></p><p><strong>Sposób użycia:</strong><p>', desc + '</p>')

    return desc


def edit_presta_product(prestashop, product: dict):
    product.pop('manufacturer_name')
    product.pop('quantity')
    product.pop('position_in_category')
    prestashop.edit('products', {'product': product})
    logging.info(f"Edited product {product['name']['language']['value']}")


def truncate_meta(text: str, max_length: int = 160) -> str:
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


def load_product_ids_from_file(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)
