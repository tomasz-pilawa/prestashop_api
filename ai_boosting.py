import xml.etree.ElementTree as ET
import random
import os
import json
import csv
import openai
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode

openai.api_key = os.getenv('openai_api')
api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


def classify_categories(product_ids_list):
    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    with open('data/temp/categories_to_classify_0.json', encoding='utf-8') as file:
        cats = json.load(file)
    cats_all = [value for key, values in cats.items() if key not in ["cat_other", "cat_old"] for value in values]

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

        # temporary for testing
        product_classification[0] = 'Pielęgnacja Twarzy'
        product_classification[1] = 'Tonik'
        product_classification[2] = 'nawilżające'

        # always adds Home Category as one of the categories for every product
        cats = ['2'] + [cats_dict[cat] for cat in product_classification]
        cats_format = [{'id': cat_id} for cat_id in cats]

        # this is needed to add association on category db as well
        cats_original = product['product']['associations']['categories']['category']
        cats_original_ids = [element['id'] for element in cats_original]
        added_cats = [c for c in cats if c not in cats_original_ids]

        for c in added_cats:
            cato = prestashop.get('categories', int(c))
            cato['category']['associations']['products']['product'].append({'id': c})
            cato['category'].pop('level_depth')
            cato['category'].pop('nb_products_recursive')
            prestashop.edit('categories', cato)

        product['product']['id_category_default'] = cats[-1]
        product['product']['associations']['categories']['category'] = cats_format

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')
        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        prestashop.edit('products', product)

    print('FINISHED PRODUCTS CLASSIFICATION')


# classify_categories(product_ids_list=[771, 772])
# classify_categories(product_ids_list=[771])
