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


def classify_category_tester(file_name='luminosa_feed.xml', max_products=5, randomness=1):

    tree = ET.parse(f'data/{file_name}')
    root = tree.getroot()

    if randomness == 1:
        selected_products = random.sample(root.findall('o'), max_products)
    else:
        selected_products = root.findall('o')[:max_products]

    with open('data/temp/categories_to_classify_0.json', encoding='utf-8') as file:
        cats = json.load(file)

    cats_all = [value for key, values in cats.items() if key not in ["cat_other", "cat_old"] for value in values]

    for p in selected_products:
        p_name = p.find('name').text
        p_link = p.get('url')
        p_desc = p.find('desc')[:500]

        print(f'\n{p_name}')

        prompt = f"1. Classify the product {p_name} to one of the MAIN categories: {cats['cat_main']}" \
                 f"2. If it's a face cosmetic classify to at least one FORM subcategory: {cats['cat_face_form']}" \
                 f"and also classify to at least one ACTION  subcategory: {cats['cat_face_action']}" \
                 f"3. If it's a body (not face) cosmetic than classify to 1-3 body subcategory: {cats['cat_body']}" \
                 f"4. If it's a hair cosmetic than classify to one and only one hair subcategory: {cats['cat_hair']}" \
                 f"5. Classify to one of those {cats['cat_random']}, only if applicable." \
                 f"\n IMPORTANT: YOU CAN ONLY USE GIVEN SUBCATEGORIES NAMES - remain case sensitive.\n" \
                 f"VERY IMPORTANT: For face care cosmetics, ensure you select at least one MAIN category AND " \
                 f"one FORM subcategory AND one ACTION subcategory (a minimum of 3 classifications in total)." \
                 f"For hair and body cosmetics, select at least one main category and the respective subcategory." \
                 f"Always respond with a comma-separated list of the selected subcategories without any additional" \
                 f"characters, new lines, or reduntant signs like []. etc. It should be easy to use in python." \
                 f"FORMAT EXAMPLE: Pielęgnacja Twarzy, Kremy do twarzy, Kosmetyki nawilżające"

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=200, temperature=0.2)
        generated_text = response.choices[0].text
        print(generated_text)

        product_classification = []

        generated_text = generated_text.split("\n\n", 1)[1]

        for part in generated_text.split(","):
            category_name = part.strip()
            if category_name in cats_all:
                product_classification.append(category_name)

        # extract main category
        product_main_cat = product_classification[-1]
        print(f'Kategoria główna: {product_main_cat}')

        print(product_classification)


# classify_category_tester(max_products=5)


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

        print('EVERYTHING WORKS EXCEPT THAT NOW CATEGORIES DICT WOULD BE NEEDED TO PAIR THEM UP')
        print('REMEMBER TO ADD HOME CATEGORY AS WELL FOR EVERY PRODUCT')

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')
        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        # print(product)



# classify_categories(product_ids_list=[771, 772])