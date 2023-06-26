import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import openai
import requests

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)

openai.api_key = os.getenv('openai_api')

name_product = 'Kolagen Naturalny Colway PLATINUM 200ml'


def test_response(data):
    prompt = f"Make 400 characters short product description for ecommerce for {data}" \
             f"It should be in Polish, in 5 bullet points saying what the product is, for which skin, " \
             f"and what are the benefits, with possible mentioning of active ingredients, without product name"
    model = "text-davinci-003"
    response = openai.Completion.create(engine=model, prompt=prompt, max_tokens=500)

    generated_text = response.choices[0].text
    print(generated_text)
    print(len(generated_text))
    print(type(generated_text))


# print(test_response('Kolagen Naturalny Colway PLATINUM 200ml'))


def dump_cats_to_file():

    # The function is no longer needed as there is a new mode in default categories function that deals with this

    # this list is final and corresponds with eveyrthing else (newer than that above) 21_06_2023

    cat_1 = ['Pielęgnacja twarzy', 'Pielęgnacja ciała', 'Kosmetyki do włosów']

    cat_1_oo = ['Zestawy kosmetyków', 'NA LATO']

    cat_1_1 = ['Kremy do twarzy', 'Serum do twarzy', 'Oczyszczanie i pielęgnacja', 'Maseczki do twarzy',
               'Peelingi do twarzy', 'Toniki i hydrolaty', 'Kolagen naturalny', 'Maski algowe do twarzy']

    cat_1_a = ['Kosmetyki łagodzące', 'Kosmetyki matujące', 'Kosmetyki na trądzik', 'Kosmetyki nawilżające',
               'Kosmetyki odżywcze', 'Kosmetyki na zmarszczki', 'Kosmetyki liftingujące', 'Kosmetyki wygładzające',
               'Kosmetyki regenerujące', 'Kosmetyki rozświetlające', 'Kosmetyki z filtrem UV',
               'Kosmetyki na przebarwienia', 'Kosmetyki antyoksydacyjne', 'Kosmetyki rewitalizujące',
               'Kosmetyki odmładzające', 'Kosmetyki ochronne', 'Kosmetyki pod oczy', 'Kosmetyki Złuczające']

    # 10
    cat_1_1_1 = ['Kremy łagodzące', 'Kremy matujące', 'Kremy przeciwtrądzikowe', 'Kremy nawilżające', 'Kremy odżywcze',
                 'Kremy przeciwzmarszczkowe', 'Kremy wygładzające', 'Kremy regenerujące', 'Kremy rozświetlające',
                 'Kremy z filtrem UV', 'Kremy na przebarwienia']

    # 7
    cat_1_1_2 = ['Serum wygładzające', 'Serum liftingujące', 'Serum rozjaśniające', 'Serum antyoksydacyjne',
                 'Serum ujędrniające', 'Serum odmładzające', 'Serum rewitalizujące']

    cat_1_2 = ['Kosmetyki do stóp', 'Peelingi do ciała', 'Kosmetyki wyszczuplające', 'Koncentraty błotne',
               'Kosmetyki na cellulit', 'Kosmetyki ujędrniające']

    cat_1_3 = ['Szampony do włosów', 'Odżywki do włosów', 'Maski do włosów', 'Stylizacja włosów',
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

    categories = {
        'cat_main': cat_1,
        'cat_face_form': cat_1_1,
        'cat_face_action': cat_1_a,
        'cat_body': cat_1_2,
        'cat_hair': cat_1_3,
        'cat_random': cat_1_oo,
        'cat_old': cat_presta_list
    }

    with open('categories_to_classify.json', 'w', encoding='utf-8') as json_file:
        json.dump(categories, json_file, ensure_ascii=False)


def test_specific_id_response(product_id=8):

    specific = prestashop.get('products', product_id)['product']
    print(specific)
    print(specific.keys())
    print(specific.values())
    print(f"\nThe name of the product is\n {specific['name']['language']['value']}")
    print(f"The reference number of the product is\n {specific['reference']}")
    print(f"The brand of the product is\n {specific['manufacturer_name']['value']}")


# test_specific_id_response(10)


def get_products(id_list=(37, 10), brand=None):         # obsolete function
    if brand:
        products_list = [prestashop.get('products', y)['product'] for y in id_list
                         if prestashop.get('products', y)['product']['manufacturer_name']['value'] == brand]
    else:
        products_list = [prestashop.get('products', y)['product'] for y in id_list]
    return products_list


def get_products_2(brand=None, to_print=0):

    with open('brands_mapped.json') as file:
        data = json.load(file)

    if brand in list(data.keys()):
        print(f"The brand exists. Processing the data...")
        indexes = data[brand]
        products = [prestashop.get('products', product_index)['product'] for product_index in indexes]
        print(f"\nThere are {len(products)} products of {brand}:\n")

        if to_print == 1:
            for product in products:
                print(product['name']['language']['value'])

        return products

    else:
        print("None brand given or the brand doesn't exist")

