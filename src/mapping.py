import json
import requests
import xml.etree.ElementTree as ET
import logging


def update_products_dict(prestashop, product_ids: list[int] = None):
    with open('../data/all_products.json', encoding='utf-8') as file:
        product_data = json.load(file)

    product_ids = product_ids or prestashop.search('products')

    modified_products = [prestashop.get('products', product_id).get('product') for product_id in product_ids]
    product_data = [p for p in product_data if int(p['id']) not in product_ids] + modified_products

    with open('../data/all_products.json', 'w', encoding='utf-8') as file:
        json.dump(product_data, file, indent=4, ensure_ascii=False)
    logging.info(f'FINISHED updating product dict. Modified {len(product_ids)} products.')


def update_brands_dict(prestashop):
    with open('../data/all_products.json', encoding='utf-8') as file:
        all_products = json.load(file)

    skus = list(set([product['reference'] for product in all_products]))
    eans = list(set([product['ean13'] for product in all_products if len(product['ean13']) > 5]))

    manufacturers_ids = prestashop.search('manufacturers')
    brand_id = {prestashop.get('manufacturers', manufacturer_id)['manufacturer']['name']: manufacturer_id
                for manufacturer_id in manufacturers_ids}

    brands_dict = {'brand_id': brand_id, 'skus': skus, 'eans': eans}

    with open('../data/brands_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(brands_dict, file, indent=4, ensure_ascii=False)
    logging.info('FINISHED updating brands_dict')


def update_cats_dict(prestashop):
    categories_ids = prestashop.search('categories')
    category_ids = {prestashop.get('categories', cat_id)['category']['name']['language']['value']: cat_id
                    for cat_id in categories_ids}
    cats_dict = {'cat_id': category_ids}

    def extract_category_ids(category_data):
        return [category['id'] for category in category_data['category']['associations']['categories']['category']]

    def get_category_names(category_id):
        return [prestashop.get('categories', cat_id)['category']['name']['language']['value'] for cat_id in
                category_id]

    cat_main = ['Pielęgnacja twarzy', 'Pielęgnacja ciała', 'Kosmetyki do włosów']
    cat_random = ['Zestawy kosmetyków', 'NA LATO']

    face_ids = extract_category_ids(prestashop.get('categories', 12))
    cat_face_form = [cat for cat in get_category_names(face_ids) if not cat.startswith('Kosmetyki')]
    cat_face_action = [cat for cat in get_category_names(face_ids) if cat.startswith('Kosmetyki')]

    body_ids = extract_category_ids(prestashop.get('categories', 14))
    cat_body = get_category_names(body_ids)

    hair_ids = extract_category_ids(prestashop.get('categories', 31))
    cat_hair = get_category_names(hair_ids)

    cats_dict['cats_classify'] = {'cat_main': cat_main, 'cat_random': cat_random, 'cat_face_form': cat_face_form,
                                  'cat_face_action': cat_face_action, 'cat_body': cat_body, 'cat_hair': cat_hair}

    with open('../data/cats_dict.json', mode='w', encoding='utf-8') as file:
        json.dump(cats_dict, file, indent=4, ensure_ascii=False)
    logging.info('FINISHED updating cats_dict')


def get_xml_from_web(source: str):
    with open(f'../data/xml_urls.json', encoding='utf-8') as file:
        url = json.load(file)[source]
    response = requests.get(url)
    if response.status_code == 200:
        xml_content = response.content
        root = ET.fromstring(xml_content)

        if source != 'luminosa':

            attrs_elements = root.findall('.//attrs/a[@name="Kod producenta"]')
            for elem in attrs_elements:
                elem.attrib['name'] = 'Kod_producenta'

            for product in root.findall('o'):
                product_sku_element = product.find("attrs/a[@name='Kod_producenta']")
                if product_sku_element is None:
                    missing_sku_element = ET.SubElement(product.find("attrs"), "a", attrib={"name": "Kod_producenta"})
                    missing_sku_element.text = "MISSING"
                product_ean_element = product.find("attrs/a[@name='EAN']")
                if product_ean_element is None:
                    missing_ean_element = ET.SubElement(product.find("attrs"), "a", attrib={"name": "EAN"})
                    missing_ean_element.text = "MISSING"

            xml_content = ET.tostring(root, encoding='utf-8')

        with open(f'data/xml/{source}_feed.xml', 'wb') as file:
            file.write(xml_content)
        logging.info(f"{source.capitalize()} XML fetched successfully!")


def update_files_and_xmls(prestashop, site: str = 'urodama', product_ids: list[int] = None):
    with open(f'../data/xml_urls.json', encoding='utf-8') as file:
        url_list = json.load(file).get(f'{site}_php_update')
    for url in url_list:
        requests.get(url)
    for xml_site in ['aleja', 'urodama', 'urodama_inci', 'luminosa']:
        get_xml_from_web(source=xml_site)

    update_products_dict(prestashop, product_ids=product_ids)
    update_brands_dict(prestashop)
    update_cats_dict(prestashop)