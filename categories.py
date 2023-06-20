import xml.etree.ElementTree as ET
import random
import os
import openai
from prestapyt import PrestaShopWebServiceDict
from unidecode import unidecode

openai.api_key = os.getenv('openai_api')
api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

cat_1 = ['Pielęgnacja twarzy', 'Pielęgnacja ciała', 'Pielęgnacja i stylizacja włosów', 'Zestawy kosmetyków']

# 8/6
cat_1_1 = ['Kremy do twarzy', 'Serum do twarzy', 'Oczyszczanie i pielęgnacja', 'Kosmetyki pod oczy',
           'Maseczki do twarzy', 'Peelingi do twarzy', 'Toniki i hydrolaty']

cat_1_a = ['kosmetyki łagodzące', 'kosmetyki matujące', 'kosmetyki na trądzik', 'kosmetyki nawilżające',
           'kosmetyki odżywcze', 'kosmetyki przeciwzmarszczkowe', 'kosmetyki liftingujące', 'kosmetyki wygładzające',
           'kosmetyki regenerujące', 'kosmetyki rozświetlające', 'kosmetyki z filtrem UV', 'kosmetyki na przebarwienia',
           'kosmetyki antyoksydacyjne', 'kosmetyki rewitalizujące', 'kosmetyki odmładzające',
           'Kosmetyki ochronne przed zanieczyszczeniami', 'kosmetyki pod oczy']

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

new_cat_dict = {"1": "Root",
                "2": "Home",
                "12": "Twarz",
                "13": "Okolice oczu",
                "14": "Ciało",
                "28": "Zestawy",
                "31": "Włosy",
                "41": "Formuła",
                "38": "Stopy",
                "60": "NA LATO",
                "15": "nawilżające",
                "16": "odmładzające",
                "17": "złuszczające",
                "18": "trądzik",
                "19": "na przebarwienia",
                "20": "odmładzające",
                "21": "nawilżające",
                "22": "wypełniające",
                "23": "cienie i obrzęki",
                "24": "wyszczuplające",
                "25": "ujędrniające",
                "26": "cellulit",
                "27": "na rozstępy",
                "32": "szampony",
                "33": "odżywki",
                "34": "maski",
                "35": "pielęgnacja",
                "36": "stylizacja",
                "37": "przeciwsłoneczne",
                "39": "pielęgnacja",
                "40": "odświeżenie",
                "42": "Krem",
                "43": "Serum",
                "44": "Ampułki",
                "45": "Balsam",
                "46": "Koncentrat błotny",
                "47": "Krem z filtrem SPF",
                "48": "Lakier",
                "49": "Maska algowa",
                "50": "Maseczka do twarzy",
                "51": "Maska do włosów",
                "52": "Mus",
                "53": "Odżywka",
                "54": "Olejek",
                "55": "Peeling",
                "56": "Puder",
                "57": "Szampon",
                "58": "Tonik",
                "59": "Żel",
                "61": "Mgiełka",
                "62": "Kolagen",
                "63": "peeling do ciała"
                }

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

print(new_cat_dict)

# try_dict = {key: value for key, value in new_cat_dict.items()}
# print(try_dict)

# for x in new_cat_dict.keys():
#     print(x)
