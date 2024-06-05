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
import pandas as pd
from src import utils
import config


class BrandExplorer:

    def __init__(self, brand: str):
        self.brand = brand
        self.all_products = utils.get_products_df_from_xml()
        self.excluded_sku, self.excluded_ean = utils.get_excluded_product_list()

    def filter_products(self):
        conditions = (
                (self.all_products['Producent'].isin([self.brand])) &
                (~self.all_products['Kod_producenta'].isin(self.excluded_sku)) &
                (~self.all_products['EAN'].isin(self.excluded_ean))
        )
        return self.all_products[conditions]

    def write_product_ideas(self, product: pd.Series):
        product_data = {
            'ID_TARGET': '',
            'SKU': product['Kod_producenta'],
            'Product Name': product['name'],
            'Active': 1,
            'Brand': self.brand,
            'Date': datetime.now().strftime("%d-%m-%Y %H:%M"),
            'EAN': product['EAN'],
            'Sales 2021': 0,
            'Sales 2022': 0,
            'COST NET': utils.calculate_net_cost(product['price']),
            'PRICE': utils.format_price(product['price']),
            'LINK': product['url'],
            'ID_SOURCE': product['id']
        }

        with open(config.product_ideas_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=product_data.keys())
            writer.writerow(product_data)

    def explore_brand(self):
        selected_products = self.filter_products()
        for index, product in selected_products.iterrows():
            self.write_product_ideas(product)


class ProductCsvProcessor:
    def __init__(self, csv_filename: str):
        self.default_data = config.default_prestashop_product_data
        self.source_data = utils.get_dict_from_csv(csv_filename)
        self.enriched_products_ids = utils.get_ids_from_dict(self.source_data)
        self.enriched_data = utils.get_products_df_from_xml(self.enriched_products_ids)

    def process_products(self) -> list[dict]:
        processed_products = []

        for product_source in self.source_data:
            product_data = self._create_product_dict(product_source)
            enriched_product = self._enrich_product(product_data)
            formatted_product = self._format_product(enriched_product)
            processed_products.append(formatted_product)

        return processed_products

    def _create_product_dict(self, product_source) -> dict:
        product_data = dict(self.default_data)

        product_data['name'] = product_source.get('Product Name')
        product_data['reference'] = product_source.get('SKU')
        product_data['ean13'] = product_source.get('EAN')
        product_data['price'] = utils.unformat_price(product_source.get('PRICE'))
        product_data['wholesale_price'] = utils.unformat_price(product_source.get('COST NET'))
        product_data['id_category_default'] = 2
        product_data['link_rewrite'] = utils.create_simple_link(product_data.get('name'))

        product_data['_Brand'] = product_source.get('Brand')
        product_data['_ID_SOURCE'] = product_source.get('ID_SOURCE')

        return product_data

    def _enrich_product(self, product_data) -> dict:
        product_data['id_manufacturer'] = utils.get_manufacturer_id(product_data.get('_Brand'))
        source_product_id = product_data.get('_ID_SOURCE', None)
        source_product_data = self.enriched_data.loc[self.enriched_data['id'] == source_product_id]

        product_data['image_url'] = source_product_data['img_url'].iloc[0]

        product_source_desc = source_product_data['desc'].iloc[0]
        product_data['description'], product_data['description_short'] = utils.make_init_desc(product_source_desc)

        product_data['meta_title'] = product_data['name']
        product_data['meta_description'] = utils.truncate_meta(product_data['description_short'])

        return product_data

    def _format_product(self, product_data) -> dict:
        product_data.pop('_Brand')
        product_data.pop('_ID_SOURCE')
        formatted_product_data = utils.apply_presta_formatting(product_data)

        return formatted_product_data


class ProductAdder:
    def __init__(self, prestashop_connector, products_to_add: list):
        self.products_to_add = products_to_add
        self.prestashop = prestashop_connector
        self.indexes_added = []

    def add_products(self):
        for product in self.products_to_add:
            self._upload_product(product)
        self._dump_indexes_to_file()

    def _upload_product(self, product):
        product_upload_data = {'product': dict(product)}
        product_upload_data['product'].pop('image_url', None)

        response = self.prestashop.add('products', product_upload_data)
        added_product_id = int(response['prestashop']['product']['id'])
        self.indexes_added.append(added_product_id)

        self._upload_product_image(product, added_product_id)

    def _upload_product_image(self, product, product_id):
        image_url = product.get('image_url', None)
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            filename = f"{product['link_rewrite']['language']['value']}{config.image_url_suffix}"
            image_content = image_response.content
            self.prestashop.add(f'/images/products/{product_id}', files=[('image', filename, image_content)])

    def _dump_indexes_to_file(self):
        with open(config.product_indexes_path, 'w') as file:
            json.dump(self.indexes_added, file)


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
                        utils.edit_presta_product(prestashop, product=target_product)
                        break
                    else:
                        logging.info(f"No INCI in the source description for product {target_product.get('name')}")
                        break

    logging.info('FINISHED Inserting INCI into selected products')


def set_unit_price_api_sql(prestashop, product_ids: list[int], site: str = 'urodama'):

    with open('data/php_access.json', encoding='utf-8') as file:
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
        conn.rollback()
    finally:
        c.close()
        conn.close()


