import json

from colorama import Fore, Back
from rm_api import API, check_file_exists, get_file, ROOT_DOC_SCHEMA
from slashr import SlashR

with open("../config.json", "r") as f:
    config = json.load(f)

api = API(
    uri=config["uri"],
    discovery_uri=config["discovery_uri"],
    token_file_path="../token",
    sync_file_path="../sync.old",
)
api.debug = True
api.check_for_document_storage()

files = get_file(api, api.get_root()["hash"], ROOT_DOC_SCHEMA)
with SlashR(False) as sr:
    for i, file in enumerate(files.files):
        sub_files = get_file(api, file.hash, file.rm_filename)
        for j, sub_file in enumerate(sub_files.files):
            if not check_file_exists(api, sub_file.hash, sub_file.rm_filename):
                print(f"File {sub_file.uuid} is missing -> {sub_file.hash}")
            else:
                sr.print(
                    f"{Back.LIGHTBLACK_EX}{Fore.YELLOW}"
                    f"[{i:^7}/{files.items:^7}]"
                    f"{Fore.MAGENTA}"
                    f"[{j:^7}/{sub_files.items:^7}]"
                    f"{Fore.GREEN} "
                    f"File {sub_file.hash} is present"
                    f"{Fore.RESET}{Back.RESET}"
                )
    sr.print(f"{Back.LIGHTBLACK_EX}{Fore.GREEN}DONE!{Fore.RESET}{Back.RESET}")
