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
    if len(text) > max_length:
        truncated_text = text[:max_length - 3] + "..."
    else:
        truncated_text = text
    return truncated_text


def select_products_xml(source='luminosa', mode=None, data=None, print_info=None):
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


# EXAMPLES OF USAGE OF THIS FUNCTION
# select_products_xml(source='luminosa', mode='brands', data=['Essente', 'Mesoestetic'], print_info=1)
# select_products_xml(source='luminosa', mode='brands', data=['Mesoestetic'], print_info=1)
# select_products_xml(source='luminosa', mode='exclude', data=[716, 31, 711, 535, 723, 55, 536, 724, 741], print_info=1)
# select_products_xml(source='luminosa', mode='include', data=[716, 31, 711, 535, 723, 55, 536, 724, 741], print_info=1)


def process_products(product_list, max_products=5):

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

    with open(file_path, encoding='utf-8', newline='') as file:
        reader = list(csv.DictReader(file))

    for r in reader:
        product = prestashop.get('products', r['ID_u'])

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

    print('FINISHED FIXING')

    return fixed_ids


def add_product_from_xml(select_source=None, select_mode=None, select_ids=None, process_max_products=2):
    products = select_products_xml(source=select_source, mode=select_mode, data=select_ids)
    products = process_products(products, max_products=process_max_products)
    add_with_photo(products)


def improve_products(file_path_fix=None, indexes_list=None, classify_ai=None, descriptions_ai=None):
    # the function can either fix products from csv or fix from csv & boost description (new products) or only boost_ai

    if file_path_fix:
        fix_data_from_csv(file_path=file_path_fix)
    else:
        # here needs to go a list of indices INT either from running select_products previously (own XML) or json_dict
        print(indexes_list)

    if classify_ai:
        pass
        # classify() ---> should encapsulate prompts and inserting properly

    if descriptions_ai:
        pass
        # write_descriptions() ---> should encapsulate prompts and inserting properly

    # update_dicts()

    pass


# improve_products(file_path_fix='data/logs/__dummy_testing_change.csv')
# improve_products(

# add_product_from_xml(select_source='luminosa', process_max_products=2)
# prestashop.delete('products', [786, 787])


def add_product(file_name, brand=None, mode='print', price_ratio=1.87, max_products=3, edit_presta=0,
                excluded_indexes=None, included_indexes=None):
    # this one actually gets XML from the file
    tree = ET.parse(f'data/{file_name}')
    root = tree.getroot()

    selected_products = []

    with open('data/brands_dict.json', encoding='utf-8') as file:
        sku_list = json.load(file)['skus']

    if brand:
        for o in root.findall('o'):
            o_brand = o.find("./attrs/a[@name='Producent']").text
            if o_brand == brand:
                selected_products.append(o)
    else:
        selected_products = root.findall('o')

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

    if included_indexes:
        new_selected_products = []
        for product in selected_products:
            product_id = int(product.get('id'))
            if product_id in included_indexes:
                new_selected_products.append(product)
        selected_products = new_selected_products

    if mode == 'print':
        print(f'\nThere are potentially {len(selected_products)} products to add from the XML file\n')
        for p in selected_products[:max_products]:
            print(p.find('name').text)
            print(p.get('id'))
            print(p.find("attrs/a[@name='Kod_producenta']").text)

    if mode == 'test' or mode == 'chat':

        default_data = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404", "condition": "new",
                        "show_price": "1", "indexed": "1", "visibility": "both"}

        with open('data/brands_dict.json', encoding='utf-8') as file:
            default_data['id_manufacturer'] = json.load(file)['brand_id'][brand]

        for single_product in selected_products[:max_products]:
            data = default_data

            data['id_category_default'] = 2
            data['reference'] = single_product.find("attrs/a[@name='Kod_producenta']").text
            data['ean13'] = single_product.find("attrs/a[@name='EAN']").text
            data['price'] = single_product.get('price')
            data['wholesale_price'] = str(round(float(data['price']) / price_ratio, 2))
            data['name'] = single_product.find('name').text
            data['link_rewrite'] = data['name'].lower().replace(' ', '-')

            if mode == 'test':
                data['description'] = single_product.find('desc').text.split('div class')[0]
                data['description_short'] = single_product.find('desc').text.split('</p><p>')[0]
                data['meta_title'] = truncate_string(data['name'], 70)
                data['meta_description'] = truncate_string(data['description'][3:].split('.')[0] + '.', 160)

            if mode == 'chat':
                prompt_description = f"Write ecommerce SEO product description {data['name']} " \
                                     f"everything in polish, around 2500 characters total\n" \
                                     f"styling as on luminosa.pl" \
                                     f"it should contain the following parts:" \
                                     f"- short description - maximum 800 characters of introduction about the product " \
                                     f"- indications and benefits (around 5-10 bullet points " \
                                     f"starting with 'Właściwości nazwa_produktu', include recommended type of skin) " \
                                     f"- składniki aktwne (bullet points with very short main benefits) " \
                                     f"- sposób użycia " \
                                     f"- skład INCI" \
                                     f"\nEach part (except introduction) should start with the bold headline " \
                                     f"and ':' at the end"
                model_description = "text-davinci-003"

                response_description = openai.Completion.create(engine=model_description,
                                                                prompt=prompt_description, max_tokens=2500)
                data['description'] = response_description.choices[0].text

                prompt_description_short = f"Write ecommerce product description of max 500 characters for " \
                                           f"{data['name']}" \
                                           f"Content: 1 bullet point introduction, 3 bullet points with benefits, " \
                                           f"1 bullet point about recommended area of use and skin type" \
                                           f"Conditions: Polish language, no product name" \
                                           f"Formatting: each bullet point with a bullet sign, no dot at the end, " \
                                           f"each from new line"
                model_description_short = "text-davinci-003"

                response_description_short = openai.Completion.create(engine=model_description_short,
                                                                      prompt=prompt_description_short, max_tokens=500)
                data['description_short'] = response_description_short.choices[0].text

                prompt_meta_title = f"Write meta title for SEO for ecommerce for the product {data['name']} " \
                                    f"The most important condition: maximum 70 characters (NEVER EXCEED THAT!) &" \
                                    f"Never include product quantity/volume (eg. 50ml, 500g, etc) &" \
                                    f"benefits in Polish language & Each word capitalized (except and, from, etc) &" \
                                    f"Always start with full brand name + most important part of the product name" \
                                    f"Optionally: include main benefit if there is space within 70 characters" \
                                    f"(if your response exceed 70 char, than don't include benefit or product series" \
                                    f"example: Nazwa Marki Seria Marki - Konsystencja + Benefit (np. Krem Regenerujący)"
                model_meta_title = "text-davinci-003"

                response_meta_title = openai.Completion.create(engine=model_meta_title,
                                                               prompt=prompt_meta_title, max_tokens=300)
                data['meta_title'] = response_meta_title.choices[0].text

                prompt_meta_description = f"Write ecommerce meta description of max 160 characters for {data['name']}" \
                                          f"Conditions: never include brand nor product name, " \
                                          f"everything in Polish language," \
                                          f"Include only main benefits and basic product info" \
                                          f"Make it attractive to click, but be factual"
                model_meta_description = "text-davinci-003"

                response_meta_description = openai.Completion.create(engine=model_meta_description,
                                                                     prompt=prompt_meta_description, max_tokens=500)
                data['meta_description'] = response_meta_description.choices[0].text

            for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
                data[x] = {'language': {'attrs': {'id': '2'}, 'value': data[x]}}

            product_info = {'product': data}
            print(product_info)

            if edit_presta == 1:
                response = prestashop.add('products', product_info)

                product_id = response['prestashop']['product']['id']
                image_url = single_product.find("imgs/main").get('url')
                filename = f"{data['link_rewrite']['language']['value']}-kosmetyki-urodama.jpg"

                response = requests.get(image_url)
                response.raise_for_status()

                image_path = "images/" + filename

                with open(image_path, "wb") as file:
                    file.write(response.content)

                with open(image_path, "rb") as file:
                    image_content = file.read()

                prestashop.add(f'/images/products/{product_id}', files=[('image', filename, image_content)])

    print('\nFunction completed')
