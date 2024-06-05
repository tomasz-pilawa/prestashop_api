import json
import re
import openai
from bs4 import BeautifulSoup
from src import processors, utils


def classify_categories(prestashop, openai_conn, product_ids_list: list[int]):
    openai.api_key = openai_conn

    with open('data/cats_dict.json', encoding='utf-8') as file:
        cats_dict = json.load(file)
    cats_classify = cats_dict.get('cats_classify')
    cats_id_dict = cats_dict.get('cat_id')

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id).get('product')
        product_desc = product['description_short']['language']['value']
        product_cats = []

        with open('data/prompts/classify_product.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product=product_desc, cats=cats_classify)

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=400, temperature=0.2)
        generated_text = response.choices[0].text

        for part in generated_text.split(","):
            category_name = part.strip()
            if category_name in list(cats_id_dict.keys()):
                product_cats.append(category_name)

        product_cats_ids = ['2'] + [cats_id_dict[cat] for cat in product_cats]
        product_cats_upload = [{'id': cat_id} for cat_id in product_cats_ids]

        product['id_category_default'] = product_cats_ids[-1]
        product['associations']['categories']['category'] = product_cats_upload

        utils.edit_presta_product(prestashop, product=product)


def write_descriptions(prestashop, openai_conn, product_ids_list: list[int]):
    openai.api_key = openai_conn

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id).get('product')
        product_name = product['name']['language']['value']
        product_desc = product['description']['language']['value']
        product_summary, product_ingredients = manipulate_desc(product_desc)

        with open('data/prompts/write_desc_2.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=product_summary)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1900, temperature=0.25)

        desc_short, desc_long = make_desc(response.choices[0].text.strip())

        with open('data/prompts/write_active.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_desc=product_ingredients)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=1500, temperature=0.25)

        desc_active = make_active(response.choices[0].text.strip())

        product['description_short']['language']['value'] = desc_short
        product['description']['language']['value'] = desc_long + desc_active

        utils.edit_presta_product(prestashop, product=product)


def write_meta(prestashop, openai_conn, product_ids_list: list[int]):
    openai.api_key = openai_conn

    for product_id in product_ids_list:
        product = prestashop.get('products', product_id)['product']
        product_name = product['name']['language']['value']
        product_desc = product['description_short']['language']['value']
        product_desc = BeautifulSoup(product_desc, 'html.parser').get_text()

        with open('data/prompts/write_meta_2.txt', 'r', encoding='utf-8') as file:
            prompt_template = file.read().strip()
        prompt = prompt_template.format(product_name=product_name, product_desc=product_desc)
        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=400, temperature=0.3)

        text = response.choices[0].text.strip()

        meta_title = text.split('META DESCRIPTION:')[0].split('META TITLE:')[1].strip()
        meta_desc = utils.truncate_meta(text.split('META DESCRIPTION:')[1].strip())

        product['meta_title']['language']['value'] = meta_title
        product['meta_description']['language']['value'] = meta_desc

        utils.edit_presta_product(prestashop, product=product)


def apply_ai_actions(prestashop, openai_conn, product_ids: list[int],
                     classify_ai: bool = 0, descriptions_ai: bool = 0, meta_ai: bool = 0, inci_unit: bool = 0):

    if classify_ai:
        classify_categories(prestashop, openai_conn, product_ids)
    if descriptions_ai:
        write_descriptions(prestashop, openai_conn, product_ids)
    if meta_ai:
        write_meta(prestashop, openai_conn, product_ids)
    if inci_unit:
        processors.fill_inci(prestashop, product_ids=product_ids, source='aleja')
        processors.set_unit_price_api_sql(prestashop, product_ids=product_ids)


def manipulate_desc(desc: str) -> tuple[str, str]:

    cleaned_text = re.sub(r'\n+(?![^\n]*:)', ' ', desc)
    cleaned_text = re.sub(r'&#\d+;', '', cleaned_text).replace('&nbsp;', '').replace('</b>', '').replace('<b>', ''). \
        replace(' •', '')

    inci_split = re.split(r'skład inci', cleaned_text, flags=re.IGNORECASE)
    if len(inci_split) >= 2:
        cleaned_text = inci_split[0].strip()

    active_split = re.split(r'składniki aktywne:', cleaned_text, flags=re.IGNORECASE)

    if len(active_split) >= 2:
        summary = active_split[0].strip()
        ingredients = active_split[1].strip()
    else:
        summary = cleaned_text
        ingredients = cleaned_text

    return summary[:3000], ingredients[:3000]


def make_desc(desc: str) -> tuple[str, str]:
    desc_short = desc.split('SHORT DESCRIPTION:')[1].strip()
    desc_long = desc.split('SHORT DESCRIPTION:')[0].replace('LONG DESCRIPTION:', '').strip(). \
        replace('Właściwości i Zalety kosmetyku:', '</p><p><strong>Właściwości i Zalety kosmetyku:</strong>')

    desc_short = re.sub(r'\n& ', r'</li><li>', desc_short)
    desc_short = re.sub(r'& ', r'<li>', desc_short)
    desc_short = f'<ul style="list-style-type: disc;">{desc_short}</li></ul>'

    desc_long = re.sub(r'\n& ', r'</li><li>', desc_long)
    desc_long = re.sub(r'\n\n', '</p><p>', desc_long)
    desc_long = desc_long.replace('</strong></li><li>', '</strong></p><ul style="list-style-type: disc;"><li>')
    desc_long = f'<p>{desc_long}</li></ul>'

    return desc_short, desc_long


def make_active(desc: str) -> str:
    desc = re.sub(r'SKŁADNIKI:',
                  r'<p></p><p><strong>Składniki aktywne:</strong></p><ul style="list-style-type: disc;">', desc)
    desc = re.sub(r'(\n&|\n-)', r'</li><li>', desc).replace('</li>', '', 1)
    desc = re.sub(r'\n\nSPOSÓB UŻYCIA:', r'</li></ul><p></p><p><strong>Sposób użycia:</strong><p>', desc + '</p>')

    return desc
