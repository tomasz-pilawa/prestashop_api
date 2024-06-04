import argparse
import glob
import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
import config
import csv
import copy


def get_products_df_from_xml(id_list: list = None):
    product_tree = ET.parse(config.xml_read.get('xml_feed_link'))
    missing_value = config.xml_read.get('missing_tag')
    products = []

    for product in product_tree.getroot().findall('o'):

        product_data = product.attrib
        for key, tag in config.xml_read.get('tags').items():
            element = product.find(tag)
            if element is not None:
                if key == 'img_url':
                    product_data[key] = element.attrib.get('url', missing_value)
                else:
                    product_data[key] = element.text.strip() if element.text else missing_value
            else:
                product_data[key] = missing_value

        attrs = product.find('attrs')
        if attrs is not None:
            for attr in attrs.findall('a'):
                if attr.get('name') in config.xml_read.get('attrs'):
                    product_data[attr.get('name')] = attr.text.strip() if attr.text else missing_value

        products.append(product_data)

    if id_list:
        products = [product for product in products if product.get('id') in id_list]

    return pd.DataFrame(products)


def get_excluded_product_list():
    with open(config.brand_dict_path, encoding='utf-8') as file:
        excluded_products_list = json.load(file)
    excluded_sku = excluded_products_list.get('skus', [])
    excluded_ean = excluded_products_list.get('eans', [])

    return excluded_sku, excluded_ean


def format_price(price):
    return str(price.replace('.', ','))


def unformat_price(price):
    return str(price.replace(',', '.'))


def calculate_net_cost(price):
    price_net = float(price) / config.net_price_factor
    rounded_price_net = round(price_net, 2)
    str_price = str(rounded_price_net)
    formated_price_net = str_price.replace('.', ',')
    return formated_price_net


def create_simple_link(name):
    simple_link = name.replace(' ', '-')
    final_link = simple_link.lower()
    return final_link


def get_dict_from_csv(csv_filename: str):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, 'data', 'logs', f'{csv_filename}.csv')
    with open(file_path, encoding='utf-8', newline='') as file:
        product_dict = list(csv.DictReader(file))
    return product_dict


def get_ids_from_dict(source_dict: dict):
    id_list = [product['ID_SOURCE'] for product in source_dict]
    return id_list


def get_manufacturer_id(brand_name: str):
    with open(config.brand_dict_path, encoding='utf-8') as file:
        brand_ids_dict = json.load(file).get('brand_id', None)
    manufacturer_id = brand_ids_dict.get(brand_name, None)
    return manufacturer_id


def make_init_desc(desc: str):
    strip_desc = desc.strip()
    long_desc = strip_desc.replace('&#8211;', '-').replace('&nbsp', '')

    clean_desc = long_desc.replace('\n', ' ')
    sentences = '.'.join(clean_desc.split('.')[:3])
    short_desc = sentences[:790] + '.'

    return long_desc, short_desc


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

    return output.strip()[:180]


def apply_presta_formatting(product_data):
    for field in config.lang_format_fields:
        formatted_field = copy.deepcopy(config.default_lang_format)
        formatted_field['language']['value'] = product_data[field]
        product_data[field] = formatted_field
    return product_data


def load_product_ids_from_file(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)
