import json
from typing import Any, Annotated

from extism import Json

from . import definitions as d
from ..shared_types import context_button_clean


# Configs
@d.host_fn()
@d.transform_to_json
def moss_em_config_get(key: str):
    return d.extension_manager.configs[d.extension_manager.current_extension].get(key)


@d.host_fn()
@d.unpack
def moss_em_config_set(key: str, value: Any):
    d.extension_manager.configs[d.extension_manager.current_extension][key] = value
    if d.extension_manager.current_extension not in d.extension_manager.dirty_configs:
        d.extension_manager.dirty_configs.append(d.extension_manager.current_extension)


@d.host_fn()
def moss_em_get_state() -> Annotated[dict, Json]:
    return json.loads(json.dumps(d.extension_manager.raw_state))


@d.host_fn()
def moss_em_register_extension_button(button: Annotated[dict, Json]):
    button["_extension"] = d.extension_manager.current_extension
    d.extension_manager.extension_buttons.append(
        context_button_clean(button, append=d.ACTION_APPEND)
    )


@d.host_fn(signature=([], []))
def moss_em_export_statistical_data(*args):
    d.extension_manager.export_statistical_data()


@d.host_fn()
@d.transform_to_json
def moss_em_loader_progress() -> float:
    if not d.gui.loader.files_to_load:
        return 1.0
    if not d.gui.loader.files_loaded:
        return 0.0
    return d.gui.loader.files_to_load / d.gui.loader.files_loaded
