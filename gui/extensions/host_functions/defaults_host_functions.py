from typing import Any, Tuple, Optional

from . import definitions as d
from ...defaults import Defaults


@d.host_fn()
@d.set_color
def moss_defaults_set_color(key: str, color: Tuple[int, ...]):
    setattr(Defaults, key, color)


@d.host_fn()
@d.get_color
def moss_defaults_get_color(key: str):
    return getattr(Defaults, key)


@d.host_fn()
@d.set_text_color
def moss_defaults_set_text_color(
    key: str, colors: Tuple[Optional[Tuple[int, ...]], ...]
):
    setattr(Defaults, key, colors)


@d.host_fn()
@d.get_text_color
def moss_defaults_get_text_color(key: str):
    return getattr(Defaults, key)


@d.host_fn()
@d.transform_to_json
def moss_defaults_get(key: str):
    return getattr(Defaults, key)


@d.host_fn()
@d.unpack
def moss_defaults_set(key: str, value: Any):
    try:
        getattr(Defaults, key)
    except AttributeError:
        if d.gui.config.debug:
            print(f"Previously unset Defaults value has been set {key}: {value}")
    setattr(Defaults, key, value)
