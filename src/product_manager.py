from src import ai_boosting, config, editing, mapping


class ProductManager:
    def __init__(self, api_connector):
        self.api_connector = api_connector
        self.mode = config.params.get('mode', 'explore')
        self.brand = config.params.get('brand', 'Mesoestetic')
        self.csv_filename = config.params.get('csv_filename', 'adding_01')

    def explore_brand(self, brand):
        editing.explore_brand(brand)

    def add_products(self, csv_filename):
        products = editing.process_products_from_csv(source_csv=csv_filename)
        editing.add_products_api(self.api_connector, product_list=products)

    def improve_products(self):
        product_ids = editing.load_product_ids_from_file('data/logs/product_indexes.json')
        ai_boosting.apply_ai_actions(self.api_connector, config.openai_key, product_ids, **config.ai_params)
        mapping.update_files_and_xmls(self.api_connector, product_ids=product_ids)

    def execute_operations(self):
        if self.mode == 'explore':
            self.explore_brand(self.brand)
        elif self.mode == 'add':
            self.add_products(self.csv_filename)
        elif self.mode == 'improve':
            self.improve_products()
        else:
            raise ValueError(f"Unknown mode '{self.mode}'.")