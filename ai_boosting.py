import os
import json
import openai
from prestapyt import PrestaShopWebServiceDict
from bs4 import BeautifulSoup

import editing

openai.api_key = os.getenv('openai_api')
api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


def classify_categories(product_ids_list):

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    with open('data/cats_dict.json', encoding='utf-8') as file:
        cats = json.load(file)['cats_classify']
    cats_all = [value for key, values in cats.items() if key not in ["cat_other", "cat_old"] for value in values]

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)['product']

        product_desc = product['description_short']['language']['value']

        with open('data/prompts/classify_product.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product=product_desc, cats=cats)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=400, temperature=0.2)
        generated_text = response.choices[0].text

        product_classification = []

        for part in generated_text.split(","):
            category_name = part.strip()
            if category_name in cats_all:
                product_classification.append(category_name)

        with open('data/cats_dict.json', encoding='utf-8') as file:
            cats_dict = json.load(file)['cats_name_id']

        cats_classified = ['2'] + [cats_dict[cat] for cat in product_classification]
        cats_format = [{'id': cat_id} for cat_id in cats_classified]

        product['id_category_default'] = cats_classified[-1]
        product['associations']['categories']['category'] = cats_format

        editing.edit_presta_product(product=product)

    print('FINISHED PRODUCTS CLASSIFICATION')


def write_descriptions_2(product_ids_list):

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)['product']
        product_name = product['name']['language']['value']
        print(product_name)

        product_desc = product['description']['language']['value']

        product_summary, product_ingredients = editing.manipulate_desc(product_desc)

        with open('data/prompts/write_desc_2.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=product_summary)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1900, temperature=0.25)

        desc_short, desc_long = editing.make_desc(response.choices[0].text.strip())

        with open('data/prompts/write_active.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_desc=product_ingredients)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1500, temperature=0.25)

        desc_active = editing.make_active(response.choices[0].text.strip())

        product['description_short']['language']['value'] = desc_short
        product['description']['language']['value'] = desc_long + desc_active

        editing.edit_presta_product(product=product)

    print('FINISHED WRITING PRODUCT DESCRIPTIONS')


def write_meta(product_ids_list):

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)['product']
        product_name = product['name']['language']['value']

        product_desc = product['description_short']['language']['value']
        product_desc = BeautifulSoup(product_desc, 'html.parser').get_text()

        print(product_name)

        with open('data/prompts/write_meta_2.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=product_desc)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=400, temperature=0.3)

        text = response.choices[0].text.strip()

        meta_title = text.split('META DESCRIPTION:')[0].split('META TITLE:')[1].strip()
        meta_desc = editing.truncate_meta(text.split('META DESCRIPTION:')[1].strip())

        product['meta_title']['language']['value'] = meta_title
        product['meta_description']['language']['value'] = meta_desc

        editing.edit_presta_product(product=product)

    print('FINISHED WRITING META DESCRIPTIONS')
