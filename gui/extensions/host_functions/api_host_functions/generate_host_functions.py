from pprint import pformat
from typing import Annotated, get_origin, Any, Dict, Callable, Tuple, get_args

import pygameextra as pe
from box import Box
from colorama import Style, Fore
from extism import Json

import rm_api
from . import accessor_handlers as ah
from . import shared_types as st
from .wrappers import check_is_dict
from .. import definitions as d


class AccessorInfo:
    def __init__(self, name, can_set, can_get, custom_setters):
        self.name = name
        self.can_set = can_set
        self.can_get = can_get
        self.custom_setters = custom_setters or {}


def generate_for_type(prefix, list_of_types):
    """
    Helper function to generate host functions for a TypedDict type.

    :param list_of_types: A list of dictionaries containing the type, item_type, item_infer and handles.

    The dictionary items should look like this:

    - t: TypedDict,
    - item_type: RMObject,
    - item_infer: Callable[[AccessorInstanceBox], Tuple[RMObject, partial]],
    - handles: List[AccessorTypes]
    """
    _items: Dict[st.AccessorTypes, AccessorInfo] = (
        {}
    )  # Maps the accessor types to the type definitions
    _function_mapping: Dict[
        st.AccessorTypes,
        Callable[[st.AccessorInstanceBox], Tuple[..., Callable[[Dict], None]]],
    ] = {}  # Maps the accessor types to the functions that handle them
    for type_to_handle in list_of_types:
        _can_get = {}
        cannot_get = {}
        _can_set = {}
        cannot_set = {}
        allowed_to_set = type_to_handle.get("allow_setting", ())
        for name, _t in type_to_handle["t"].__annotations__.items():
            is_dict = check_is_dict(_t)

            if is_dict:
                _original = _t
                _t = Annotated[_original, Json]

            _can_get[name] = _t

            if name not in allowed_to_set and (
                (is_dict and _original not in (st.TRM_Zoom,))
                or (prop := getattr(type_to_handle["item_type"], name, None))
                and isinstance(prop, property)
                and prop.fset is None
                or (
                    get_origin(_t) is list
                    and not _t.__args__[0] in (int, str, float, st.TRM_Tag)
                )
            ):
                cannot_set[name] = _t
                continue

            _can_set[name] = _t

        _item_info = AccessorInfo(
            type_to_handle["item_type"].__name__,
            _can_set,
            _can_get,
            type_to_handle.get("custom_setters"),
        )

        for handle in type_to_handle["handles"]:
            _items[handle] = _item_info
            _function_mapping[handle] = type_to_handle["item_infer"]

        if pe.settings.config.debug_log:
            print(
                f"Generated host functions for `{Style.BRIGHT}{type_to_handle['t'].__name__}{Style.NORMAL}` "
                f"please note the following restrictions:\n"
                f"CANNOT SET: {Fore.LIGHTGREEN_EX}{pformat(cannot_set)}{Fore.RESET}\n"
                f"CANNOT GET: {Fore.LIGHTYELLOW_EX}{pformat(cannot_get)}{Fore.RESET}"
            )

    # noinspection PyBroadException
    @d.host_fn(f"{prefix}_get")
    @d.transform_to_json
    def _func(accessor: Annotated[st.AccessorInstance, Json], key: str):
        try:
            accessor_type = st.AccessorTypes(accessor["type"])
            item_info = _items[accessor_type]
            obj, _ = _function_mapping[accessor_type](Box(accessor))
            value_type = item_info.can_get.get(key, None)
            if not value_type:
                raise ValueError(f"Can't get {key} from {item_info.name}")

            if check_is_dict(value_type):
                return getattr(obj, key).__dict__
            return getattr(obj, key)
        except Exception as e:
            d.extension_manager.error(
                f"Failed to [get]<{key}> with {accessor} {e.__class__.__name__}"
            )
            raise e

    # noinspection PyBroadException
    @d.host_fn(f"_{prefix}_set")
    @d.unpack
    def _func(
        accessor: Annotated[st.AccessorInstance, Json],
        key: str,
        value: Annotated[Any, Json],
    ):
        try:
            accessor_type = st.AccessorTypes(accessor["type"])
            item_info = _items[accessor_type]
            obj, _ = _function_mapping[accessor_type](Box(accessor))
            value_type = item_info.can_set.get(key, None)
            if not value_type:
                raise ValueError(f"Can't set {key} on {item_info.name}")
            if not isinstance(value, get_args(value_type) or value_type):
                raise ValueError(
                    f"Can't set {key} on {item_info.name} "
                    f"because type {type(value)} "
                    f"does not match required type {value_type}"
                )
            if custom_setter := item_info.custom_setters.get(key):
                return custom_setter(obj, accessor, value)
            return setattr(obj, key, value)
        except Exception as e:
            d.extension_manager.error(
                f"Failed to [set]<{key}><{value if d.try_len(value) < 100 else '...'}> with {accessor} {e.__class__.__name__}"
            )
            raise e

    # noinspection PyBroadException
    @d.host_fn(f"{prefix}_get_all")
    @d.debug_result
    @d.transform_to_json
    def _func(accessor: Annotated[st.AccessorInstance, Json]) -> Annotated[Any, Json]:
        try:
            obj, accessor_adder = _function_mapping[st.AccessorTypes(accessor["type"])](
                Box(accessor)
            )
            final_data = obj.__dict__
            accessor_adder(final_data)
            return final_data
        except Exception as e:
            d.extension_manager.error(
                f"Failed to [get_all] with {accessor} {e.__class__.__name__}"
            )
            raise e


# Top most objects
generate_for_type(
    "moss_api",
    [
        {
            "t": st.TRM_Document,
            "item_type": rm_api.Document,
            "item_infer": ah.document_inferred,
            "handles": [
                st.AccessorTypes.APIDocument,
                st.AccessorTypes.StandaloneDocument,
            ],
        },
        {
            "t": st.TRM_DocumentCollection,
            "item_type": rm_api.DocumentCollection,
            "item_infer": ah.collection_inferred,
            "handles": [
                st.AccessorTypes.APICollection,
                st.AccessorTypes.StandaloneCollection,
            ],
        },
        {
            "t": st.TRM_MetadataDocument,
            "item_type": rm_api.Metadata,
            "item_infer": ah.metadata_inferred,
            "handles": [
                st.AccessorTypes.APIDocumentMetadata,
                st.AccessorTypes.APICollectionMetadata,
                st.AccessorTypes.StandaloneDocumentMetadata,
                st.AccessorTypes.StandaloneCollectionMetadata,
                st.AccessorTypes.StandaloneMetadata,
            ],
        },
        {
            "t": st.TRM_Content,
            "item_type": rm_api.Content,
            "item_infer": ah.content_inferred,
            "handles": [
                st.AccessorTypes.APIDocumentContent,
                st.AccessorTypes.StandaloneDocumentContent,
                st.AccessorTypes.StandaloneContent,
            ],
        },
        {
            "t": st.API_FileSyncProgress,
            "item_type": rm_api.FileSyncProgress,
            "item_infer": ah.file_sync_progress_inferred,
            "handles": [st.AccessorTypes.FileSyncProgress],
            "custom_setters": {"stage": ah.SyncExtensionFunctionHelper.set_stage},
        },
        {
            "t": st.API_DocumentSyncProgress,
            "item_type": rm_api.DocumentSyncProgress,
            "item_infer": ah.document_sync_progress_inferred,
            "handles": [st.AccessorTypes.DocumentSyncProgress],
        },
        {
            "t": st.API_SyncStage,
            "item_type": ah.SyncExtensionFunctionHelper,
            "item_infer": ah.sync_stage_inferred,
            "handles": [st.AccessorTypes.SyncStage],
            "allow_setting": ("text", "icon"),
        },
    ],
)
