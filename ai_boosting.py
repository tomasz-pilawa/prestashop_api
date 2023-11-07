import xml.etree.ElementTree as ET
import random
import os
import json
import re
import csv
import openai
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode

import editing

openai.api_key = os.getenv('openai_api')
api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


def classify_categories(product_ids_list):
    """
    The function takes list of product IDS and classifies them to predefined categories using chat-gpt API.
    It pairs the names of the categories with their IDs in the shop and directly reassigns them via Prestashop API.
    It adds associations both in categories and products tables, which is necessary.
    It assigns main category and all categories.
    :param product_ids_list: list of integers (must be valid Prestashop product ids)
    :return: prints success message (it operates directly on products and doesn't return anything
    """
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    with open('data/cats_dict.json', encoding='utf-8') as file:
        cats = json.load(file)['cats_classify']
    cats_all = [value for key, values in cats.items() if key not in ["cat_other", "cat_old"] for value in values]

    # print(type(cats))

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)

        # it is used inside the prompt
        product_name = product['product']['name']['language']['value']

        with open('data/prompts/classify_product.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, cats=cats)

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=200, temperature=0.2)
        generated_text = response.choices[0].text
        # print(generated_text)

        product_classification = []

        for part in generated_text.split(","):
            category_name = part.strip()
            if category_name in cats_all:
                product_classification.append(category_name)

        # extract main category
        product_main_cat = product_classification[-1]
        print(f'Kategoria główna: {product_main_cat}')
        print(product_classification)

        # pairing up classified categories with their respective IDs in Prestashop based on Dict
        with open('data/cats_dict.json', encoding='utf-8') as file:
            cats_dict = json.load(file)['cats_name_id']

        # always adds Home Category as one of the categories for every product
        cats_classified = ['2'] + [cats_dict[cat] for cat in product_classification]
        cats_format = [{'id': cat_id} for cat_id in cats_classified]
        print(cats_classified)

        product['product']['id_category_default'] = cats_classified[-1]
        product['product']['associations']['categories']['category'] = cats_format

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')
        product['product'].pop('position_in_category')
        # if not product['product']['position_in_category']['value'].isdigit():
        #     product['product']['position_in_category']['value'] = '1'
        # if int(product['product']['position_in_category']['value']) < 1:
        #     product['product']['position_in_category']['value'] = str(1)

        print(product)
        prestashop.edit('products', product)

    print('FINISHED PRODUCTS CLASSIFICATION')


def write_descriptions(product_ids_list):
    """
    The function takes list of product IDS & improves short description, description, meta title & meta description.
    It uses chat-gpt API to accomplish that and directly edits given products via Prestashop API.
    :param product_ids_list: list of integers (must be valid Prestashop product ids)
    :return: prints success message (it operates directly on products and doesn't return anything)
    """
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)
        product_name = product['product']['name']['language']['value']
        product_desc = product['product']['description']['language']['value']

        if product_desc.count(' ') > 350:
            tokens = product_desc.split(' ')
            product_desc = ' '.join(tokens[:350])

        # print(product)
        print(product_name)

        with open('data/prompts/write_descriptions.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=product_desc)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1800, temperature=0.25)
        print(f"TOKENS USED: {response['usage']['total_tokens']}")
        # print(response.choices[0].text.strip())

        description_short = response.choices[0].text.strip().split('*****')[0].replace('SHORT DESCRIPTION', '').strip()
        description = response.choices[0].text.strip().split('*****')[1].replace('LONG DESCRIPTION', '').strip()
        # print(description_short)
        # print(description)

        product['product']['description_short']['language']['value'] = description_short
        product['product']['description']['language']['value'] = description

        with open('data/prompts/write_meta.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=description_short)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1000, temperature=0.1)
        print(f"TOKENS USED: {response['usage']['total_tokens']}")
        # print(response.choices[0].text.strip())

        meta_title = response.choices[0].text.strip().split('*****')[0].replace('META TITLE', '').strip()
        meta_description = response.choices[0].text.strip().split('*****')[1].replace('META DESCRIPTION', '').strip()
        # print(meta_title)
        # print(meta_description)

        product['product']['meta_description']['language']['value'] = meta_description
        product['product']['meta_title']['language']['value'] = meta_title

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')
        if not product['product']['position_in_category']['value'].isdigit():
            product['product']['position_in_category']['value'] = '1'
        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        prestashop.edit('products', product)

    print('FINISHED WRITING PRODUCT DESCRIPTIONS')


def make_desc(desc):

    if desc is None:
        with open('data/prompts/z_product_desc.txt', 'r', encoding='utf-8') as file:
            desc = file.read().strip()

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

    # print(desc_short)
    # print(desc_long)

    return desc_short, desc_long

# make_desc(desc=None)


def make_active(desc):

    if desc is None:
        with open('data/prompts/z_product_active.txt', 'r', encoding='utf-8') as file:
            desc = file.read().strip()

    desc = re.sub(r'SKŁADNIKI:',
                  r'<p></p><p><strong>Składniki aktywne:</strong></p><ul style="list-style-type: disc;">', desc)
    desc = re.sub(r'(\n&|\n-)', r'</li><li>', desc).replace('</li>', '', 1)

    # desc = desc.replace('SKŁADNIKI:</li><li>',
    #                     '<p></p><p><strong>Składniki aktywne:</strong></p><ul style="list-style-type: disc;"><li>')

    desc = re.sub(r'\n\nSPOSÓB UŻYCIA:', r'</li></ul><p></p><p><strong>Sposób użycia:</strong><p>', desc + '</p>')

    # print(desc)
    return desc


# make_active(desc=None)


def edit_presta_product(product):

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    product.pop('manufacturer_name')
    product.pop('quantity')
    if not product['position_in_category']['value'].isdigit():
        product['position_in_category']['value'] = '1'
    if int(product['position_in_category']['value']) < 1:
        product['position_in_category']['value'] = str(1)

    prestashop.edit('products', {'product': product})

    print(f"Edited product {product['name']['language']['value']}")


def write_descriptions_2(product_ids_list, reset_desc):
    """
    The function takes list of product IDS & improves short description, description, meta title & meta description.
    It uses chat-gpt API to accomplish that and directly edits given products via Prestashop API.

    Improved 2.0 function will take original product description, trim it of redundant characters and split into
    two parts: descriptions vs active ingredients & mode of use. It will than send separate and optimized api requests
    to open AI and get several components of the whole product description.
    It will do the proper formatting and arrange the parts rather than use unreliable openAI fantasies.
    The function will be faster, the formatting will always be right and will use less tokens.

    :type reset_desc: bool
    :param product_ids_list: list of integers (must be valid Prestashop product ids)
            reset_desc: should it get the descriptions from alejazdrowia_inci (recommended for testing)
    :return: prints success message (it operates directly on products and doesn't return anything)
    """

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)['product']
        product_name = product['name']['language']['value']
        print(product_name)

        if reset_desc == 1:
            product_ean = product['ean13'].strip()
            tree = ET.parse(f'data/aleja_inci_feed.xml')
            root = tree.getroot()
            source_products = root.findall('o')

            matching_product = next((product for product in source_products if
                                     product.find("attrs/a[@name='EAN']").text.strip() == product_ean), None)
            if matching_product:
                product_desc = matching_product.find('desc').text.lower()
                print('Reset description')
            else:
                product_desc = product['description']['language']['value']
        else:
            product_desc = product['description']['language']['value']

        product_summary, product_ingredients = editing.manipulate_desc(product_desc)
        print(product_summary)

        with open('data/prompts/write_desc_2.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=product_summary)
        print(f'{len(prompt)/2.5} TOKESN APRX')
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1900, temperature=0.25)
        # print(f"TOKENS USED: {response['usage']['total_tokens']}")
        print(response.choices[0].text.strip())

        desc_short, desc_long = make_desc(response.choices[0].text.strip())

        with open('data/prompts/write_active.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_desc=product_ingredients)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1500, temperature=0.25)
        # print(f"TOKENS USED: {response['usage']['total_tokens']}")
        print(response.choices[0].text.strip())

        desc_active = make_active(response.choices[0].text.strip())

        product['description_short']['language']['value'] = desc_short
        product['description']['language']['value'] = desc_long + desc_active

        edit_presta_product(product=product)

    print('FINISHED WRITING PRODUCT DESCRIPTIONS')


write_descriptions_2(product_ids_list=[819, 820, 821, 822], reset_desc=True)

