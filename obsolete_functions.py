import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import openai
import requests
import xml.etree.ElementTree as ET
import json

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

    with open('data/brands_dict.json', encoding='utf-8') as file:
        data = json.load(file)['brand_index']

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


def add_product_from_csv(product):
    with open(product) as file:
        reader = csv.reader(file)
        header = next(reader)
        row = next(reader)
        data = dict(zip(header, row))

    with open('data/brands_dict.json', encoding='utf-8') as file:
        id_manufacturer = json.load(file)['brand_id'][data['manufacturer_name']]

    data['id_manufacturer'] = id_manufacturer
    data['wholesale_price'] = str(round(int(data['price']) / 1.87, 2))
    data['link_rewrite'] = data['name'].lower().replace(' ', '-')

    default_values = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404", "condition": "new",
                    "show_price": "1", "indexed": "1", "visibility": "both"}

    data.update(default_values)

    data.pop('manufacturer_name')

    for x in ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']:
        data[x] = {'language': {'attrs': {'id': '2'}, 'value': data[x]}}

    print('Inserting the product...')

    product_info = {'product': data}
    print(product_info)
    prestashop.add('products', product_info)

    return data


def get_categories_dict():
    # very obsolete function, not used anywhere when moved

    category_ids = prestashop.search('categories')
    category_names = [[prestashop.get('categories', m)['category']['name']['language']['value'],
                       prestashop.get('categories', m)['category']['id_parent']] for m in category_ids]

    category_dict = dict(zip(category_ids, category_names))

    with open('data/categories_dict.json', 'w') as file:
        json.dump(category_dict, file)


def get_init_sku_dict():
    # move all functionality to new brands_dict

    indexes = prestashop.search('products')

    products_list = [prestashop.get('products', y)['product'] for y in indexes]
    sku_list = []
    brands = []

    for product in products_list:
        sku_list.append(product['reference'])
        if not product['manufacturer_name']['value']:
            product['manufacturer_name']['value'] = 'Z_MISSING'
        brands.append(product['manufacturer_name']['value'])

    result = {}
    for brand, product in zip(brands, sku_list):
        result.setdefault(brand, []).append(product)
    result['indexes_used'] = sku_list

    with open('data/sku_mapped.json', 'w') as file:
        json.dump(result, file)

    return result


def get_init_brand_dict():
    # move all functionality to new brands_dict (even though at the moment of moving dict seems unused)

    indexes = prestashop.search('products')

    products_list = [prestashop.get('products', y)['product'] for y in indexes]
    indexes_used = []
    brands_used = []

    for product in products_list:
        indexes_used.append(product['id'])
        if not product['manufacturer_name']['value']:
            product['manufacturer_name']['value'] = 'Z_MISSING'
        brands_used.append(product['manufacturer_name']['value'])

    result = {}
    for brand, product in zip(brands_used, indexes_used):
        result.setdefault(brand, []).append(int(product))
    result['indexes_used'] = indexes_used

    with open('data/brands_mapped.json', 'w') as file:
        json.dump(result, file)

    return result


def get_manufacturers_dict():
    # move all functionality to new brands_dict

    manufacturer_ids = prestashop.search('manufacturers')
    manufacturer_names = [prestashop.get('manufacturers', m)['manufacturer']['name'] for m in manufacturer_ids]

    manufacturer_dict = dict(zip(manufacturer_names, manufacturer_ids))

    with open('data/manufacturers_dict.json', 'w') as file:
        json.dump(manufacturer_dict, file)

    return manufacturer_dict


def update_brands_dict():
    # immediately obsolete as better idea emerged (to operate directly on all_products.json)

    idx = prestashop.search('products')

    products_list = [prestashop.get('products', y)['product'] for y in idx[:10]]
    indexes = []
    skus = []
    brands = []

    for product in products_list:
        indexes.append(product['id'])
        skus.append(product['reference'])
        if not product['manufacturer_name']['value']:
            product['manufacturer_name']['value'] = 'Z_MISSING'
        brands.append(product['manufacturer_name']['value'])

    brands_dict = {}

    indexes_dict = {}
    for brand, product in zip(brands, indexes):
        indexes_dict.setdefault(brand, []).append(int(product))
    brands_dict['indexes'] = indexes_dict

    skus_dict = {}
    for brand, product in zip(brands, skus):
        skus_dict.setdefault(brand, []).append(product)
    brands_dict['skus'] = skus_dict

    brands_dict['all_sku'] = skus
    brands_dict['all_index'] = indexes
    brands_dict['all_brands'] = brands

    with open('data/brands_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(brands_dict, file)


def get_xml_obsolete(source='luminosa', from_web=0):

    if from_web == 1:
        with open(f'data/xml_urls.json') as file:
            url = json.load(file)[source]
        response = requests.get(url)
        if response.status_code == 200:
            with open(f'data/{source}_feed.xml', 'wb') as file:
                file.write(response.content)
            print("File saved successfully!")
        else:
            print("Failed to fetch the XML file!")

    # OLD FUNCTIONALITY THAT IS NOT BEING USED NOW

    brand = "Germaine de Capuccini"
    selected_products = []

    tree = ET.parse(f'data/luminosa_feed.xml')
    root = tree.getroot()

    for o in root.findall('o'):
        producent = o.find("./attrs/a[@name='Producent']").text
        if producent == brand:
            selected_products.append(o)

    for product in selected_products:
        name = product.find('name').text
        sku = product.find("attrs/a[@name='Kod_producenta']").text
        print(name)
        print(sku)

    # print(ET.tostring(selected_products[3], encoding='unicode', method='xml'))


def create_csv_file(file_path):
    headers = ['ID_u', 'ref', 'nazwa', 'active', 'brand', 'wprowadzony', 'Comments', 'Sales 2021', 'Sales 2022',
               'COST NET', 'PRICE']

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)


# create_csv_file('data/logs/added_products_raw.csv')

