import mapping
import editing as e
import ai_boosting

params = {'mode': 'improve',
          'brand': 'Anna Lotan',
          'csv_filename': 'test_adding'}
ai_params = dict(classify_ai=1, descriptions_ai=0, meta_ai=0, inci_unit=0)


if __name__ == "__main__":
    mode = params.get('mode')

    if mode == 'explore':
        e.explore_brand(params.get('brand'))

    elif mode == 'add':
        products = e.process_products_from_csv(source_csv=params.get('csv_filename'))
        e.add_with_photo(product_list=products)

    elif mode == 'improve':
        product_ids = e.load_product_ids_from_file('data/logs/product_indexes.json')
        ai_boosting.apply_ai_actions(product_ids, **ai_params)
        mapping.update_files_and_xmls(product_ids=product_ids)
