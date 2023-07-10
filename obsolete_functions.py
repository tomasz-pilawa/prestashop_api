import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import openai
import requests
import xml.etree.ElementTree as ET
import json

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)

openai.api_key = os.getenv('openai_api')


def fix_prices(limit=2, file=None):

    """
    Function that takes xml of an old shop with correct prices and updates them on the new shop.
    It was an ad-hoc emergency script that needed to update all the prices quickly as there were errors in migration.
    Limit parameter can be used for testing
    """

    tree = ET.parse(f'data/temp/{file}')
    root = tree.getroot()

    all_products = root.findall('o')

    for p in all_products[:limit]:
        p_name = p.find('name').text
        p_id = int(p.get('id'))
        p_price = p.get('price')

        product = prestashop.get('products', p_id)

        product['product']['price'] = p_price

        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')

        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        product['product']['price'] = p_price
        print(product['product'])

        prestashop.edit('products', product)


# fix_prices(limit=800, file='new_prices_urodama_07_2023.xml')


def fix_stock(file_old=None, file_new=None):

    """
    Similarly to fix_prices function, this one was created ad-hoc to quickly correct some mistakes in database migration
    It takes to xml-files and compares the ids of the products on both of them.
    Based on that, it disables products directly on the new shop API so the data is coherent
    """

    prestashop = PrestaShopWebServiceDict(api_url, api_key)

    tree_old = ET.parse(f'data/temp/{file_old}')
    root_old = tree_old.getroot()
    all_products_old = root_old.findall('o')
    indexes_old = [int(p.get('id')) for p in all_products_old]

    tree_new = ET.parse(f'data/temp/{file_new}')
    root_new = tree_new.getroot()
    all_products_new = root_new.findall('o')
    indexes_new = [int(p.get('id')) for p in all_products_new]

    indexes_to_disable = [i for i in indexes_new if i not in indexes_old]
    products_to_disable = [p for p in all_products_new if int(p.get('id')) in indexes_to_disable]

    for p in products_to_disable:
        p_id = int(p.get('id'))

        product = prestashop.get('products', p_id)

        product['product']['active'] = 0
        product['product'].pop('manufacturer_name')
        product['product'].pop('quantity')

        if int(product['product']['position_in_category']['value']) < 1:
            product['product']['position_in_category']['value'] = str(1)

        print(product['product'])

        prestashop.edit('products', product)


# fix_stock(file_old='new_prices_urodama_07_2023.xml', file_new='ceneo_urodama_after_update_too_many.xml')


def add_product(file_name, brand=None, mode='print', price_ratio=1.87, max_products=3, edit_presta=0,
                excluded_indexes=None, included_indexes=None):
    """
    This was first main and workable function with many functionalities including getting the products data from XML,
    processing it, improving descriptions via AI and directly adding product with an image via Prestashop API.

    The functionalities were encapsulated in various  functions for better code clarity.
    Now the whole process of adding a new product is ALWAYS a process:
    - add_product_from_xml (select_products_xml, process_products, add_with_photo) - adds a new basic product and
        returns a csv for manual formatting
    - editing csv manually - ensure manually in Google Sheets that a product name, brand and prices are adequate
    - improve_products - fixes manual csv edits and perform ai boosting (classification, description, features)
        and then updates dictionaries and throws a log of performed changes

    New structure makes everything more clear, flexible, and it won't be needed to write separate functions for editing
    old products, adding new ones or making ad hoc simple changes in prices
    """

    tree = ET.parse(f'data/{file_name}')
    root = tree.getroot()

    selected_products = []

    with open('data/brands_dict.json', encoding='utf-8') as file:
        sku_list = json.load(file)['skus']

    if brand:
        for o in root.findall('o'):
            o_brand = o.find("./attrs/a[@name='Producent']").text
            if o_brand == brand:
                selected_products.append(o)
    else:
        selected_products = root.findall('o')

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

        default_data = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404", "condition": "new",
                        "show_price": "1", "indexed": "1", "visibility": "both"}

        with open('data/brands_dict.json', encoding='utf-8') as file:
            default_data['id_manufacturer'] = json.load(file)['brand_id'][brand]

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

            if edit_presta == 1:
                response = prestashop.add('products', product_info)

                product_id = response['prestashop']['product']['id']
                image_url = single_product.find("imgs/main").get('url')
                filename = f"{data['link_rewrite']['language']['value']}-kosmetyki-urodama.jpg"

                response = requests.get(image_url)
                response.raise_for_status()

                image_path = "images/" + filename

                with open(image_path, "wb") as file:
                    file.write(response.content)

                with open(image_path, "rb") as file:
                    image_content = file.read()

                prestashop.add(f'/images/products/{product_id}', files=[('image', filename, image_content)])

    print('\nFunction completed')


def classify_category_tester(file_name='luminosa_feed.xml', max_products=5, randomness=1):

    """
    The function was used to test chat-gpt classification of products to certain categories based on XML products.
    Replaced by new classify_categories() function in ai_boosting that takes ids of the products to classify,
    gets prompt from separate txt file, pairs with category id in Prestashop and edits directly via API.
    """

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

    """
    The function is no longer needed as there is a new mode in default categories function that deals with this
    """

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
    """
    very old function for learning
    """
    specific = prestashop.get('products', product_id)['product']
    print(specific)
    print(specific.keys())
    print(specific.values())
    print(f"\nThe name of the product is\n {specific['name']['language']['value']}")
    print(f"The reference number of the product is\n {specific['reference']}")
    print(f"The brand of the product is\n {specific['manufacturer_name']['value']}")


# test_specific_id_response(10)

def get_products_2(brand=None, to_print=0):
    """
    Old learning function that returns all products from a certain brand based on brands dict
    """
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
    """
    Old learning function that takes a product in a csv and adds it directly via Prestashop API
    """

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


def pair_sku_id():
    """
    It's designed to be used once to pair SKU and ID in the new show after migration.
    """
    with open('data/all_products.json', encoding='utf-8') as file:
        data = json.load(file)
    result = {product['reference']:product['id'] for product in data}
    print(result)


# pair_sku_id()


def get_init_sku_dict():
    """
    Old function - now this functionality is directly in update_brands_dict
    """
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
    """
    Old function - now this functionality is directly in update_brands_dict
    """
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


def update_brands_dict():
    """
    Old function - now this functionality is directly in update_brands_dict
    """
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
    """
    There is more efficient function that serves the same purpose
    """
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
    """
    Function used to reset the added_products_raw log file after testing
    """
    headers = ['ID_u', 'ref', 'nazwa', 'active', 'brand', 'wprowadzony', 'Comments', 'Sales 2021', 'Sales 2022',
               'COST NET', 'PRICE']

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)


# create_csv_file('data/logs/added_products_raw.csv')

