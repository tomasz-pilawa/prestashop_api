import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import xml.etree.ElementTree as ET
import openai
import api_products as ap

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

openai.api_key = os.getenv('openai_api')

prestashop = PrestaShopWebServiceDict(api_url, api_key)


def truncate_string(text, max_length=70):
    if len(text) > max_length:
        truncated_text = text[:max_length - 3] + "..."
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
    data['wholesale_price'] = str(round(int(data['price']) / 1.87, 2))
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


def add_from_xml(file_name, brand, mode='print', price_ratio=1.87, max_products=3, add_product=0,
                 excluded_indexes=None, included_indexes=None):
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

            if add_product == 1:
                prestashop.add('products', product_info)

    print('\nFunction completed')


add_from_xml(file_name='luminosa_feed.xml', brand='Germaine de Capuccini', mode='chat', max_products=50,
             included_indexes=[720, 718])
# prestashop.delete('products', 778)
