import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET
import api_products as ap

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


def truncate_string(text, max_length=70):
    if len(text) > max_length:
        truncated_text = text[:max_length-3] + "..."
    else:
        truncated_text = text
    return truncated_text


def add_product_from_csv(product):

    with open(product) as file:
        reader = csv.reader(file)
        header = next(reader)
        row = next(reader)
        data = dict(zip(header, row))

    with open('manufacturers_dict.json') as man_file:
        id_manufacturer = json.load(man_file)[data['manufacturer_name']]

    data['id_manufacturer'] = id_manufacturer
    data['wholesale_price'] = str(round(int(data['price'])/1.87, 2))
    data['link_rewrite'] = data['name'].lower().replace(' ', '-')

    with open('default_product_values.json') as def_file:
        default_values = json.load(def_file)

    data.update(default_values)

    data.pop('manufacturer_name')

    for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
        data[x] = {'language': {'attrs': {'id': '2'}, 'value': data[x]}}

    print('Inserting the product...')

    product_info = {'product': data}
    print(product_info)
    prestashop.add('products', product_info)

    return data


def add_from_xml(file_name, brand, mode='print', price_ratio=1.87, max_products=3, excluded_indexes=None):

    tree = ET.parse(file_name)
    root = tree.getroot()

    selected_products = []

    for o in root.findall('o'):
        o_brand = o.find("./attrs/a[@name='Producent']").text
        if o_brand == brand:
            selected_products.append(o)

    with open('sku_mapped.json') as file:
        sku_list = json.load(file)[brand]

    for product in selected_products:
        product_sku = product.find("attrs/a[@name='Kod_producenta']").text
        if product_sku in sku_list:
            selected_products.remove(product)

    if excluded_indexes:
        selected_products_copy = selected_products[:]
        for product in selected_products_copy:
            product_id = int(product.get('id'))
            if product_id in excluded_indexes:
                selected_products.remove(product)

    if mode == 'print':
        print(f'\nThere are potentially {len(selected_products)} products to add from the XML file\n')
        for p in selected_products[:max_products]:
            print(p.find('name').text)
            print(p.get('id'))
            print(p.find("attrs/a[@name='Kod_producenta']").text)

    if mode == 'test':

        with open('default_product_values.json') as def_file:
            default_data = json.load(def_file)

        with open('manufacturers_dict.json') as man_file:
            default_data['id_manufacturer'] = json.load(man_file)[brand]

        for single_product in selected_products[:max_products]:
            data = default_data

            data['id_category_default'] = 2
            data['reference'] = single_product.find("attrs/a[@name='Kod_producenta']").text
            data['ean13'] = single_product.find("attrs/a[@name='EAN']").text
            data['price'] = single_product.get('price')
            data['wholesale_price'] = str(round(float(data['price'])/price_ratio, 2))
            data['name'] = single_product.find('name').text
            data['link_rewrite'] = data['name'].lower().replace(' ', '-')
            data['description'] = single_product.find('desc').text.split('div class')[0]
            data['description_short'] = single_product.find('desc').text.split('</p><p>')[0]

            data['meta_title'] = truncate_string(data['name'], 70)
            data['meta_description'] = truncate_string(data['description'][3:].split('.')[0] + '.', 160)

            for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
                data[x] = {'language': {'attrs': {'id': '2'}, 'value': data[x]}}

            product_info = {'product': data}
            print(product_info)

            if mode == 'add':
                prestashop.add('products', product_info)

    print('\nFunction completed')


add_from_xml(file_name='luminosa_feed.xml', brand='Germaine de Capuccini', mode='print', max_products=50,
             excluded_indexes=[575, 716, 541, 723, 724])
# prestashop.delete('products', 778)
