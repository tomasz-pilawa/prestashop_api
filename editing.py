import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET
import openai
import requests

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


# select_products_xml(source='luminosa', mode='brands', data=['Essente', 'Mesoestetic'], print_info=1)
# select_products_xml(source='luminosa', mode='brands', data=['Mesoestetic'], print_info=1)
# select_products_xml(source='luminosa', mode='exclude', data=[716, 31, 711, 535, 723, 55, 536, 724, 741], print_info=1)
# select_products_xml(source='luminosa', mode='include', data=[716, 31, 711, 535, 723, 55, 536, 724, 741], print_info=1)

# products = select_products_xml(source='luminosa', print_info=1)
# for element in products[:5]:
#     print(ET.tostring(element, encoding='unicode'))


def process_products(product_list, max_products=5):

    default_data = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404", "condition": "new",
                    "show_price": "1", "indexed": "1", "visibility": "both"}

    with open('data/brands_dict.json', encoding='utf-8') as file:
        manufacturer_dict = json.load(file)['brand_id']

    price_ratio = 1.87

    processed_products = []

    for single_product in product_list[:max_products]:
        data = default_data

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


# products = select_products_xml(source='luminosa', print_info=1)
# process_products(products, max_products=10)


def add_with_photo(product_list):

    indexes_added = []

    for single_product in product_list:
        for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
            single_product[x] = {'language': {'attrs': {'id': '2'}, 'value': single_product[x]}}

        product_info = {'product': single_product}

        print(single_product)

        response = prestashop.add('products', product_info)
        product_id = response['prestashop']['product']['id']
        indexes_added.append(product_id)

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

    print('SUCCESS!!! Indexes added:')
    print(indexes_added)

    return indexes_added


products = select_products_xml(source='luminosa', print_info=1)
products = process_products(products, max_products=3)
# add_with_photo(products)

# prestashop.delete('products', [790, 791])


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
