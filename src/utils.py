import argparse
import glob
import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
import config


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


def get_products_df_from_xml(source: str):
    product_tree = ET.parse(config.xml_feed_link.format(source))
    products = []

    for product in product_tree.getroot().findall('o'):
        product_data = product.attrib
        name_element = product.find('name')
        product_data['name'] = name_element.text.strip() if name_element is not None else 'MISSING'

        attrs = product.find('attrs')
        if attrs is not None:
            for attr in attrs.findall('a'):
                if attr.get('name') in ['Producent', 'Kod_producenta', 'EAN']:
                    product_data[attr.get('name')] = attr.text.strip() if attr.text else 'MISSING'

        products.append(product_data)

    return pd.DataFrame(products)


def get_excluded_product_list():
    with open(config.json_helper, encoding='utf-8') as file:
        excluded_products_list = json.load(file)
    excluded_sku = excluded_products_list.get('skus', [])
    excluded_ean = excluded_products_list.get('eans', [])

    return excluded_sku, excluded_ean


def format_price(price):
    return str(price.replace('.', ','))


def calculate_net_cost(price):
    price_net =  float(price) / config.net_price_factor
    rounded_price_net = round(price_net, 2)
    str_price = str(rounded_price_net)
    formated_price_net = str_price.replace('.', ',')
    return formated_price_net

