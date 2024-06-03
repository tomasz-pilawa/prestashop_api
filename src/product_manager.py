from src import ai_boosting, mapping, utils
from src.editing import BrandExplorer, ProductCsvProcessor, ProductAdder
import config


class ProductManager:
    def __init__(self, api_connector):
        self.api_connector = api_connector

    def execute_operations(self, mode, param):
        if mode == 'explore':
            self.explore_brand(brand=param)
        elif mode == 'add':
            self.add_products(csv_filename=param)
        elif mode == 'improve':
            self.improve_products()
        else:
            raise ValueError(f"Unknown mode '{mode}'.")

    def explore_brand(self, brand):
        BrandExplorer(brand=brand).explore_brand()

    def add_products(self, csv_filename):
        processed_products = ProductCsvProcessor(csv_filename=csv_filename).process_products()
        adder = ProductAdder(prestashop_connector=self.api_connector, products_to_add=processed_products)
        adder.add_products()

    def improve_products(self):
        product_ids = utils.load_product_ids_from_file('data/logs/product_indexes.json')
        ai_boosting.apply_ai_actions(self.api_connector, config.openai_key, product_ids, **config.ai_params)
        mapping.update_files_and_xmls(self.api_connector, product_ids=product_ids)
