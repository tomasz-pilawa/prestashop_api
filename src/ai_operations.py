import json
import re
import openai
from bs4 import BeautifulSoup

import config
from src import utils


class BoosterAI:
    def __init__(self, prestashop_connector, product_ids: list):
        openai.api_key = config.openai_key
        self.prestashop = prestashop_connector
        self.product_ids = product_ids

    def apply_ai_actions(self, classify_ai: bool = False, descriptions_ai: bool = False, meta_ai: bool = False):

        for product_id in self.product_ids:
            product, product_name, product_desc, product_desc_short = self._load_product_data(product_id)

            if classify_ai:
                id_category_default, associations_categories = self._format_categories(product_desc_short)
                product['id_category_default'] = id_category_default
                product['associations']['categories']['category'] = associations_categories

            if descriptions_ai:
                description_short, description = self._format_descriptions(product_name, product_desc)
                product['description_short']['language']['value'] = description_short
                product['description']['language']['value'] = description

            if meta_ai:
                meta_title, meta_description = self._format_meta(product_name, product_desc_short)
                product['meta_title']['language']['value'] = meta_title
                product['meta_description']['language']['value'] = meta_description

            utils.edit_presta_product(self.prestashop, product=product)

    def _format_descriptions(self, product_name: str, product_desc: str):
        product_summary, product_ingredients = manipulate_desc(product_desc)

        prompt = self._load_prompt(prompt_name='prompt_description', product_name=product_name,
                                   product_desc=product_summary)
        desc_response = self._generate_response(prompt, max_tokens=config.max_tokens_description)
        description_short, desc_long = make_desc(desc_response)

        prompt = self._load_prompt(prompt_name='prompt_description_enrichment', product_desc=product_ingredients)
        active_response = self._generate_response(prompt, max_tokens=config.max_tokens_enrichment)
        desc_active = make_active(active_response)
        description = desc_long + desc_active

        return description_short, description

    def _format_meta(self, product_name: str, product_desc: str):
        product_desc_clean = BeautifulSoup(product_desc, features='html.parser').get_text()
        prompt = self._load_prompt(prompt_name='prompt_meta', product_name=product_name,
                                   product_desc=product_desc_clean)
        meta_response = self._generate_response(prompt, max_tokens=config.max_tokens_meta)

        meta_title = meta_response.split('META DESCRIPTION:')[0].split('META TITLE:')[1].strip()
        meta_description = utils.truncate_meta(meta_response.split('META DESCRIPTION:')[1].strip())

        return meta_title, meta_description

    def _format_categories(self, product_desc: str):
        cats_classify, cat_ids = self._load_cats_dict()

        prompt = self._load_prompt(prompt_name='prompt_classification', product_desc=product_desc, cats=cats_classify)
        generated_text = self._generate_response(prompt, max_tokens=config.max_tokens_classification)

        product_cats = [cat.strip() for cat in generated_text.split(",") if cat.strip() in cat_ids]
        product_cats_ids = ['2'] + [cat_ids[cat] for cat in product_cats]
        product_cats_upload = [{'id': cat_id} for cat_id in product_cats_ids]

        return product_cats_ids[-1], product_cats_upload

    def _load_product_data(self, product_id: int):
        product = self.prestashop.get('products', product_id).get('product')
        product_name = product['name']['language']['value']
        product_desc = product['description']['language']['value']
        product_desc_short = product['description_short']['language']['value']
        return product, product_name, product_desc, product_desc_short

    @staticmethod
    def _generate_response(prompt: str, max_tokens: int):
        response = openai.ChatCompletion.create(
            model=config.openai_default_model,
            messages=[
                {"role": "system", "content": config.openai_default_role},
                {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=config.openai_default_temp
        )
        return response.choices[0].message['content'].strip()

    @staticmethod
    def _load_cats_dict():
        with open(config.cats_dict_filepath, encoding='utf-8') as file:
            cats_dict = json.load(file)
        cats_classify = cats_dict.get('cats_classify')
        cat_ids = cats_dict.get('cat_id')
        return cats_classify, cat_ids

    @staticmethod
    def _load_prompt(prompt_name: str, **kwargs) -> str:
        prompt_template = config.ai_prompts.get(prompt_name, "")
        return prompt_template.format(**kwargs)


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
