import mapping
import editing as e
import ai_boosting
import os
import openai
from prestapyt import PrestaShopWebServiceDict
from dotenv import load_dotenv

load_dotenv()
api_url = os.getenv('URODAMA_LINK')
api_key = os.getenv('URODAMA_KEY')
openai_key = os.getenv('OPENAI_KEY')

params = {'mode': 'improve',
          'brand': 'Anna Lotan',
          'csv_filename': 'test_adding'}
ai_params = dict(classify_ai=1, descriptions_ai=1, meta_ai=1, inci_unit=0)


if __name__ == "__main__":
    prestashop = PrestaShopWebServiceDict(api_url, api_key)
    mode = params.get('mode')

    if mode == 'explore':
        e.explore_brand(params.get('brand'))

    elif mode == 'add':
        products = e.process_products_from_csv(source_csv=params.get('csv_filename'))
        e.add_products_api(prestashop, product_list=products)

    elif mode == 'improve':
        product_ids = e.load_product_ids_from_file('data/logs/product_indexes.json')
        ai_boosting.apply_ai_actions(prestashop, openai_key, product_ids, **ai_params)
        mapping.update_files_and_xmls(prestashop, product_ids=product_ids)
