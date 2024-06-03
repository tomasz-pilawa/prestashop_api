import argparse
import glob
import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
import config
import csv
import copy


def load_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", help="Mode to operate the system.", type=str, default='explore', required=False)
    parser.add_argument("--param", help="Brand to explore or CSV filename.", type=str, default=None)
    args = parser.parse_args()

    if args.mode == 'explore':
        return args.mode, args.param or 'Mesoestetic'
    elif args.mode == 'add':
        if not args.param:
            args.param = get_newest_csv_name()
        return args.mode, args.param
    else:
        raise ValueError(f"Unknown mode '{args.mode}'.")


def get_newest_csv_name():

    base_dir = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.abspath(os.path.join(base_dir, os.pardir))
    csv_folder = os.path.join(parent_dir, 'data', 'logs')
    csv_filenames = sorted(glob.glob(os.path.join(csv_folder, '*.csv')), reverse=True)
    csv_filename = csv_filenames[0] if csv_filenames else None
    basename = os.path.basename(csv_filename)
    filename, ext = os.path.splitext(basename)

    return filename


def get_products_df_from_xml(source: str, id_list: list = None):
    product_tree = ET.parse(config.xml_feed_link.format(source))
    products = []

    for product in product_tree.getroot().findall('o'):
        product_data = product.attrib
        get_dict_from_csv
        name_element = product.find('name')
        product_data['name'] = name_element.text.strip() if name_element is not None else 'MISSING'

        desc_element = product.find('desc')
        product_data['desc'] = desc_element.text if desc_element is not None else 'MISSING'

        img_url = product.find('imgs/main')
        product_data['img_url'] = img_url.attrib['url'] if img_url is not None else 'MISSING'

        attrs = product.find('attrs')
        if attrs is not None:
            for attr in attrs.findall('a'):
                if attr.get('name') in ['Producent', 'Kod_producenta', 'EAN']:
                    product_data[attr.get('name')] = attr.text.strip() if attr.text else 'MISSING'

        products.append(product_data)

    if id_list:
        products = [product for product in products if product.get('id') in id_list]

    return pd.DataFrame(products)


def get_excluded_product_list():
    with open(config.json_helper, encoding='utf-8') as file:
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
    # os.chdir("../")
    with open(config.json_helper, encoding='utf-8') as file:
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
