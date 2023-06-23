import xml.etree.ElementTree as ET
import random
import os
import json
import csv
import openai
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode

openai.api_key = os.getenv('openai_api')
api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

cat_1 = ['Pielęgnacja twarzy', 'Pielęgnacja ciała', 'Kosmetyki do włosów', 'Zestawy kosmetyków']

cat_1_1 = ['Kremy do twarzy', 'Serum do twarzy', 'Oczyszczanie i pielęgnacja', 'Kosmetyki pod oczy',
           'Maseczki do twarzy', 'Peelingi do twarzy', 'Toniki i hydrolaty', 'Kolagen naturalny']

cat_1_a = ['Kosmetyki łagodzące', 'Kosmetyki matujące', 'Kosmetyki na trądzik', 'Kosmetyki nawilżające',
           'Kosmetyki odżywcze', 'Kosmetyki na zmarszczki', 'Kosmetyki liftingujące', 'Kosmetyki wygładzające',
           'Kosmetyki regenerujące', 'Kosmetyki rozświetlające', 'Kosmetyki z filtrem UV', 'Kosmetyki na przebarwienia',
           'Kosmetyki antyoksydacyjne', 'Kosmetyki rewitalizujące', 'Kosmetyki odmładzające',
           'Kosmetyki ochronne', 'Kosmetyki pod oczy', 'Kosmetyki Złuczające', 'Kosmetyki pod oczy']

cat_1_1_1 = ['Kremy łagodzące', 'Kremy matujące', 'Kremy przeciwtrądzikowe', 'Kremy nawilżające', 'Kremy odżywcze',
             'Kremy przeciwzmarszczkowe', 'Kremy wygładzające', 'Kremy regenerujące', 'Kremy rozświetlające',
             'Kremy z filtrem UV', 'Kremy na przebarwienia']

cat_1_1_2 = ['Serum wygładzające', 'Serum liftingujące', 'Serum rozjaśniające', 'Serum antyoksydacyjne',
             'Serum ujędrniające', 'Serum odmładzające', 'Serum rewitalizujące']

cat_1_2 = ['Kosmetyki do stóp', 'Peelingi do ciała', 'Wyszczuplanie i ujędrnianie', 'Koncentraty błotne',
           'Kosmetyki na cellulit']

cat_1_3 = ['Szampony do włosów', 'Odżywki do włosów', 'Maski do włosów', 'Kosmetyki do stylizacji włosów',
           'Olejki i serum do włosów', 'Ampułki do włosów']

cat_presta_list = ['Root', 'Home',
                   'Twarz', 'Okolice oczu', 'Ciało', 'Zestawy', 'Włosy', 'Stopy', 'Formuła', 'NA LATO',
                   'nawilżające', 'odmładzające', 'złuszczające', 'trądzik', 'na przebarwienia',
                   'odmładzające', 'nawilżające', 'wypełniające', 'cienie i obrzęki',
                   'wyszczuplające', 'ujędrniające', 'cellulit', 'na rozstępy',
                   'szampony', 'odżywki', 'maski', 'pielęgnacja', 'stylizacja', 'przeciwsłoneczne',
                   'pielęgnacja', 'odświeżenie',
                   'Krem', 'Serum', 'Ampułki', 'Balsam', 'Koncentrat błotny', 'Krem z filtrem SPF', 'Lakier',
                   'Maska algowa', 'Maseczka do twarzy', 'Maska do włosów', 'Mus', 'Odżywka', 'Olejek', 'Peeling',
                   'Puder', 'Szampon', 'Tonik', 'Żel', 'Mgiełka', 'Kolagen', 'peeling do ciała']

cat_1_1t = cat_1_1_1 + cat_1_1_2 + cat_1_1[2:]

cats_all = cat_1_1t + cat_1_2 + cat_1_3


def simple_cat_classifier(file_name='luminosa_feed.xml', max_products=5, randomness=1):
    tree = ET.parse(file_name)
    root = tree.getroot()

    if randomness == 1:
        selected_products = random.sample(root.findall('o'), max_products)
    else:
        selected_products = root.findall('o')[:max_products]

    with open('categories_to_classify_0.json', encoding='utf-8') as file:
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

        # x = generated_text.strip()
        # lst = [part.strip().replace('\n', '').replace(':', '') for part in x.split(',')]
        # lst_2 = [x for x in lst if x in cat_1 + cats_all]
        #
        # print(lst_2)


# simple_cat_classifier(max_products=5)


def main_cat_classifier(file_name='luminosa_feed.xml', max_products=5, randomness=1):

    # this function is depreciated as main cat will be extracted from categories_classifier

    tree = ET.parse(file_name)
    root = tree.getroot()

    if randomness == 1:
        selected_products = random.sample(root.findall('o'), max_products)
    else:
        selected_products = root.findall('o')[:max_products]

    for p in selected_products:
        p_name = p.find('name').text

        print(f'\n{p_name}')

        prompt = f"Firstly, decided{p_name}" \
                 f"to only one, most relevant, main ecommerce category" \
                 f"from the following choices: {cats_all}" \
                 f"YOU CAN ONLY USE GIVEN CATEGORIES NAMES\n" \
                 f"Focus on more specialized categories like anti-aging, wrinkles instead of moisturizing\n" \
                 f"If it's a set, always classify as 'Zestawy kosmetyków'\n" \
                 f"Always assign at least one category\n" \
                 f"Respond with one-item list with the selected category without additional characters"

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=200, temperature=0.2)
        generated_text = response.choices[0].text
        print(generated_text)

        x = generated_text.strip()
        lst = [part.strip().replace('\n', '').replace(':', '') for part in x.split(',')]
        lst_2 = [x for x in lst if x in cat_1 + cats_all]

        print(lst_2)


# print(main_cat_classifier(max_products=3))


def category_tree_setter(mode='initial'):

    if mode == 'initial':

        cat_id = 12

        prestashop = PrestaShopWebServiceDict(api_url, api_key)

        modified_cat = prestashop.get('categories', cat_id)
        print(modified_cat)

        modified_cat['category']['name']['language']['value'] = 'Pielęgnacja Twarzy'

        link_rewritten = unidecode(modified_cat['category']['name']['language']['value'].lower().replace(' ', '-'))
        modified_cat['category']['link_rewrite']['language']['value'] = link_rewritten

        print(modified_cat)

        modified_cat['category'].pop('level_depth')
        modified_cat['category'].pop('nb_products_recursive')

        # prestashop.edit('categories', modified_cat)

    if mode == 'from_dict':
        print("serious stuff")


# category_tree_setter()


def create_json_from_csv_cats(csv_name='cats_pairing_init.csv', version='0', dump_cats_classify=0):

    version = str(version)
    data = []

    with open(csv_name, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)

    json_name = f"{csv_name.split('_')[0]}_{csv_name.split('_')[1]}_v_{version}.json"

    with open(json_name, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print('JSON file saved successfully')

    if dump_cats_classify == 1:

        categories = {
            'cat_main': [],
            'cat_face_form': [],
            'cat_face_action': [],
            'cat_body': [],
            'cat_hair': [],
            'cat_random': [],
            'cat_other': [],
            'cat_old': []
        }

        for row in data:

            category_type = row['Type']
            category_name = row['NameNew']
            categories['cat_old'].append(row['NameOld'])

            if category_type == 'main':
                categories['cat_main'].append(category_name)
            elif category_type == 'face_form':
                categories['cat_face_form'].append(category_name)
            elif category_type == 'face_action':
                categories['cat_face_action'].append(category_name)
            elif category_type == 'body':
                categories['cat_body'].append(category_name)
            elif category_type == 'hair':
                categories['cat_hair'].append(category_name)
            elif category_type == 'random':
                categories['cat_random'].append(category_name)
            else:
                categories['cat_other'].append(category_name)

        categories['cat_old'] = [c for c in categories['cat_old'] if c not in ['None']]

        cats_classify_filename = f'categories_to_classify_{version}.json'

        with open(cats_classify_filename, 'w', encoding='utf-8') as json_file:
            json.dump(categories, json_file, ensure_ascii=False)

        print('Categories to Clasify dumped into JSON too')


