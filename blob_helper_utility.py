import json
import os

from blob_mounting_helper_utility import BlobMappingUtility

_CONFIG_FILE_PATH = os.getenv("BLOB_MOUNTING_CONFIGURATIONS_JSON_PATH", None)
_AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", None)

if _CONFIG_FILE_PATH:
    with open(_CONFIG_FILE_PATH) as f:
        blob_mounting_configurations_list = json.load(f)["blob_mounting_configurations"]
    blob_mapping_utility = BlobMappingUtility(blob_mounting_configurations_list, _AZURE_STORAGE_ACCOUNT_KEY)

else:
    blob_mapping_utility = BlobMappingUtility([], _AZURE_STORAGE_ACCOUNT_KEY)
