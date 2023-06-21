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

# 8/6
cat_1_1 = ['Kremy do twarzy', 'Serum do twarzy', 'Oczyszczanie i pielęgnacja', 'Kosmetyki pod oczy',
           'Maseczki do twarzy', 'Peelingi do twarzy', 'Toniki i hydrolaty', 'Kolagen naturalny']

cat_1_a = ['Kosmetyki łagodzące', 'Kosmetyki matujące', 'Kosmetyki na trądzik', 'Kosmetyki nawilżające',
           'Kosmetyki odżywcze', 'Kosmetyki na zmarszczki', 'Kosmetyki liftingujące', 'Kosmetyki wygładzające',
           'Kosmetyki regenerujące', 'Kosmetyki rozświetlające', 'Kosmetyki z filtrem UV', 'Kosmetyki na przebarwienia',
           'Kosmetyki antyoksydacyjne', 'Kosmetyki rewitalizujące', 'Kosmetyki odmładzające',
           'Kosmetyki ochronne', 'Kosmetyki pod oczy', 'Kosmetyki Złuczające', 'Kosmetyki ']

# 10
cat_1_1_1 = ['Kremy łagodzące', 'Kremy matujące', 'Kremy przeciwtrądzikowe', 'Kremy nawilżające', 'Kremy odżywcze',
             'Kremy przeciwzmarszczkowe', 'Kremy wygładzające', 'Kremy regenerujące', 'Kremy rozświetlające',
             'Kremy z filtrem UV', 'Kremy na przebarwienia']

# 7
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

    # print(f'\nThere are potentially {len(selected_products)} products to add from the XML file\n')
    # for p in selected_products:
    #     print(p.find('name').text)
    #     print(p.get('id'))
    #     print(p.find("attrs/a[@name='Kod_producenta']").text)

    for p in selected_products:
        p_name = p.find('name').text
        p_link = p.get('url')
        p_desc = p.find('desc')[:500]

        print(f'\n{p_name}')

        prompt = f"Classify the product {p_name} to one of the main categories: {cat_1}" \
                 f"and minimum number of relatable subcategories.\n" \
                 f"If it's not a set, than choose only from one subcategories set:" \
                 f"{cat_1_2}, {cat_1_3}, {cat_1_1}\n" \
                 f"Determine if it's a cream or a serum. " \
                 f"-If it's a cream, chose 1-3 most relevant only from this set: {cat_1_1_1}." \
                 f"-If it's a serum, chose 1-3 most relevant only from this set: {cat_1_1_2}.\n" \
                 f"If it's not a set, you can never have 'serum' and 'krem' subcategories together" \
                 f"If it's a set, you can classify more freely." \
                 f"\n IMPORTANT: It's better to classify to less categories, but more accurately AND " \
                 f"YOU CAN ONLY USE GIVEN SUBCATEGORIES NAMES\n" \
                 f"Respond with one comma separated list without additional characters"

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=500, temperature=0)
        generated_text = response.choices[0].text

        x = generated_text.strip()
        lst = [part.strip().replace('\n', '').replace(':', '') for part in x.split(',')]
        lst_2 = [x for x in lst if x in cat_1 + cats_all]

        print(lst_2)


# simple_cat_classifier(max_products=3)


def main_cat_classifier(file_name='luminosa_feed.xml', max_products=5, randomness=1):
    tree = ET.parse(file_name)
    root = tree.getroot()

    if randomness == 1:
        selected_products = random.sample(root.findall('o'), max_products)
    else:
        selected_products = root.findall('o')[:max_products]

    for p in selected_products:
        p_name = p.find('name').text

        print(f'\n{p_name}')

        prompt = f"Classify the product {p_name} to only one, most relevant, main ecommerce category" \
                 f"from the following choices: {cats_all}" \
                 f"YOU CAN ONLY USE GIVEN CATEGORIES NAMES\n" \
                 f"Focus on more specialized categories like anti-aging, wrinkles instead of moisturizing\n" \
                 f"If it's a set, always classify as 'Zestawy kosmetyków'\n" \
                 f"Always assign at least one category\n" \
                 f"Respond with one-item list with the selected category without additional characters"

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=500, temperature=0)
        generated_text = response.choices[0].text

        x = generated_text.strip()
        lst = [part.strip().replace('\n', '').replace(':', '') for part in x.split(',')]
        lst_2 = [x for x in lst if x in cat_1 + cats_all]

        print(lst_2)


# print(main_cat_classifier(max_products=3))


def category_setter(cat_id=12):

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


# category_setter()


def create_json_from_csv_cats(csv_name='cats_pairing_init.csv', version='0'):

    version = str(version)
    data = []

    with open(csv_name, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)

    json_name = f"{csv_name.split('_')[0]}_{csv_name.split('_')[1]}_v_{version}.json"

    with open(json_name, 'w') as file:
        json.dump(data, file, indent=4)

    print('JSON file saved successfully')


# create_json_from_csv_cats(csv_name='cats_pairing_init.csv')
