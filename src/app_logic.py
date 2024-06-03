from src import ai_operations, mapping, utils
from src.product_processing import BrandExplorer, ProductCsvProcessor, ProductAdder
import config
import os, glob, argparse


class ProductManager:
    def __init__(self, api_connector):
        self.api_connector = api_connector

    def execute_operations(self, mode, param):
        if mode == 'explore':
            self._explore_brand(brand=param)
        elif mode == 'add':
            self._add_products(csv_filename=param)
        elif mode == 'improve':
            self._improve_products()
        else:
            raise ValueError(f"Unknown mode '{mode}'.")

    def _explore_brand(self, brand):
        BrandExplorer(brand=brand).explore_brand()

    def _add_products(self, csv_filename):
        processed_products = ProductCsvProcessor(csv_filename=csv_filename).process_products()
        adder = ProductAdder(prestashop_connector=self.api_connector, products_to_add=processed_products)
        adder.add_products()

    def _improve_products(self):
        product_ids = utils.load_product_ids_from_file('data/logs/product_indexes.json')
        ai_operations.apply_ai_actions(self.api_connector, config.openai_key, product_ids, **config.ai_params)
        mapping.update_files_and_xmls(self.api_connector, product_ids=product_ids)

    def load_parameters(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--mode", help="Mode to operate the system.", type=str, default='explore', required=False)
        parser.add_argument("--param", help="Brand to explore or CSV filename.", type=str, default=None)
        args = parser.parse_args()

        if args.mode == 'explore':
            return args.mode, args.param or 'Mesoestetic'
        elif args.mode == 'add':
            if not args.param:
                args.param = self._get_newest_csv_name()
            return args.mode, args.param
        else:
            raise ValueError(f"Unknown mode '{args.mode}'.")

    def _get_newest_csv_name(self):

        base_dir = os.path.abspath(os.path.dirname(__file__))
        parent_dir = os.path.abspath(os.path.join(base_dir, os.pardir))
        csv_folder = os.path.join(parent_dir, 'data', 'logs')
        csv_filenames = sorted(glob.glob(os.path.join(csv_folder, '*.csv')), reverse=True)
        csv_filename = csv_filenames[0] if csv_filenames else None
        basename = os.path.basename(csv_filename)
        filename, ext = os.path.splitext(basename)

        return filename
