import config
from src.app_logic import ProductManager
from src.utils import load_parameters
from prestapyt import PrestaShopWebServiceDict


if __name__ == "__main__":
    api_connector = PrestaShopWebServiceDict(config.api_url, config.api_key)
    pm = ProductManager(api_connector)
    mode, param = pm.load_parameters()
    pm.execute_operations(mode, param)
