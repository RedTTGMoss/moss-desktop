import base64
import inspect
import random
from functools import wraps, partial
from json import JSONDecodeError
from typing import (
    TYPE_CHECKING,
    Annotated,
    Optional,
    Tuple,
    Union,
    List,
    get_origin,
    Callable,
    Any,
)

import extism
import pygameextra as pe
from box import Box
from colorama import Fore, Style
from extism import host_fn as extism_host_fn, Json, ValType
from extism.extism import HOST_FN_REGISTRY

from rm_api.storage.common import FileHandle
from ..shared_types import TValue
from ..shared_types import (
    color_from_tuple,
    color_to_tuple,
    TTextColors,
    TColor,
    text_colors_to_tuple,
)
from ...events import MossFatal

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API
    from ..extension_manager import ExtensionManager

extension_manager: "ExtensionManager"
host_functions = set()
gui: "GUI"
api: "API"

_original_extism_map_arg: Callable[..., Tuple[ValType, Callable]] = getattr(
    extism.extism, "_map_arg"
)
_original_extism_map_ret: Callable[..., Tuple[ValType, Callable]] = getattr(
    extism.extism, "_map_ret"
)
ACTION_APPEND = "__em_action_"


class InvalidAccessor(ValueError):
    def __init__(self):
        super().__init__("An invalid accessor was provided for this function or check.")


def set_extism_map_arg(value=None):
    setattr(extism.extism, "_map_arg", value or _original_extism_map_arg)


def set_extism_map_ret(value=None):
    setattr(extism.extism, "_map_ret", value or _original_extism_map_ret)


def init_host_functions(_extension_manager: "ExtensionManager"):
    global gui, api, extension_manager
    extension_manager = _extension_manager
    gui = _extension_manager.gui
    api = gui.api


def try_len(obj: Any):
    try:
        return len(obj)
    except TypeError:
        return 0


def transform_to_json(fn):
    fn.__annotations__["return"] = Annotated[TValue, Json]

    @wraps(fn)
    def wrapped(*args, **kwargs) -> Annotated[TValue, Json]:
        return {"value": fn(*args, **kwargs)}

    return wrapped


def statistical_call_tracker(name: str = None):
    def wrapper(fn):
        host_functions.add(fn_name := name or fn.__name__)

        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            extension_calls = extension_manager.call_statistics.get(
                extension_manager.current_extension
            )
            if not extension_calls:
                extension_calls = {function_name: 0 for function_name in host_functions}
                extension_manager.call_statistics[
                    extension_manager.current_extension
                ] = extension_calls
            extension_calls[fn_name] = extension_calls.get(fn_name, 0) + 1
            return fn(*args, **kwargs)

        return wrapped_fn

    return wrapper


def host_fn(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    signature: Optional[Tuple[List[ValType], List[ValType]]] = None,
    user_data: Optional[Union[bytes, List[bytes]]] = None,
):
    issue_occurred_parsing_arguments = False
    argument_index = -1

    @wraps(_original_extism_map_arg)
    def handle_json_errors_arg(function_name, *args1, **kwargs1):
        # Modify the mapper to add debugging to the lambda functions
        nonlocal argument_index, issue_occurred_parsing_arguments
        _, call_function = _original_extism_map_arg(*args1, **kwargs1)
        argument_index += 1

        @wraps(call_function)
        def wrapped_call_function(
            index, *args2, **kwargs2
        ):  # Modify the lambda function to add debugging
            nonlocal issue_occurred_parsing_arguments
            try:
                return call_function(*args2, **kwargs2)
            except JSONDecodeError:
                extension_manager.error(
                    f"Please check that you are passing the correct arguments for {function_name}. "
                    f"Expected a serializable object for argument[{index}]"
                )
                api.spread_event(MossFatal)
                issue_occurred_parsing_arguments = True

        return _, partial(wrapped_call_function, argument_index)

    @wraps(_original_extism_map_ret)
    def handle_json_errors_ret(function_name, *args1, **kwargs1):
        # Modify the mapper to add debugging to the lambda functions
        nonlocal argument_index, issue_occurred_parsing_arguments
        call_functions = _original_extism_map_ret(*args1, **kwargs1)

        for i, (_, call_function) in enumerate(call_functions):

            @wraps(call_function)
            def wrapped_call_function(
                index, *args2, **kwargs2
            ):  # Modify the lambda function to add debugging
                nonlocal issue_occurred_parsing_arguments
                try:
                    return call_function(*args2, **kwargs2)
                except AttributeError:
                    extension_manager.error(
                        f"Please check that you are accepting the correct returns for {function_name}. "
                        f"Expected some object for return item[{index}]"
                    )
                    api.spread_event(MossFatal)
                    issue_occurred_parsing_arguments = True

            call_functions[i] = (_, partial(wrapped_call_function, i))

        return call_functions

    extism_wrapper = extism_host_fn(name, namespace, signature, user_data)

    @wraps(extism_wrapper)
    def wrapped_extism(fn):
        if pe.settings.config.allow_statistics:
            fn = statistical_call_tracker(name)(fn)
        if pe.settings.config.debug_log:
            sig = inspect.signature(fn)
            params = ", ".join(
                str(
                    param.annotation.__args__[0]
                    if get_origin(param.annotation) is Annotated
                    else param
                )
                for param in sig.parameters.values()
            )
            return_annotation = (
                (
                    sig.return_annotation.__args__[0]
                    if get_origin(sig.return_annotation) is Annotated
                    else sig.return_annotation
                )
                if sig.return_annotation is not sig.empty
                else None
            )
            try:
                return_type = (
                    f" -> {return_annotation.__name__}" if return_annotation else ""
                )
            except:
                return_type = " -> ???"
            print(
                f"{Style.BRIGHT}\033[4m{Fore.YELLOW}"
                f"HOST FUNCTION - {name or fn.__name__}({params}){return_type}"
                f"{Fore.RESET}{Style.NORMAL}"
            )
        return extism_wrapper(fn)

    @wraps(wrapped_extism)
    def wrapped(fn):
        set_extism_map_arg(partial(handle_json_errors_arg, name or fn.__name__))
        set_extism_map_ret(partial(handle_json_errors_ret, name or fn.__name__))

        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            nonlocal issue_occurred_parsing_arguments
            if issue_occurred_parsing_arguments:
                issue_occurred_parsing_arguments = False
                return
            return fn(*args, **kwargs)

        result = wrapped_extism(wrapped_fn)
        set_extism_map_arg()
        set_extism_map_ret()
        setattr(HOST_FN_REGISTRY[-1], "moss", True)

        return result

    return wrapped


def unpack(fn):
    fn.__annotations__.pop("key")
    fn.__annotations__["value"] = Annotated[dict, Json]
    for i, annotation in enumerate(fn.__annotations__.keys()):
        if annotation == "value":
            args_index = i
            break
    fn.__name__ = f"_{fn.__name__}"

    @wraps(fn)
    def wrapped(*args, **kwargs):
        args_left, value, args_right = (
            args[:args_index],
            args[args_index],
            args[args_index + 1 :],
        )
        return fn(*args_left, value["key"], value["value"], *args_right, **kwargs)

    return wrapped


def debug_result(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        result = fn(*args, **kwargs)
        if pe.settings.config.debug_log:
            print(
                f"{Fore.MAGENTA}HOST FUNCTION{Fore.RESET} - {fn.__name__} result: {result}"
            )
        return result

    return wrapped


def set_color(fn):
    fn.__annotations__ = {"key": str, "color": Annotated[TColor, Json]}

    @wraps(fn)
    def wrapped(key: str, color: Annotated[TColor, Json]):
        return fn(key, color_to_tuple(color))

    return wrapped


def get_color(fn):
    fn.__annotations__ = {"key": str, "return": Annotated[TColor, Json]}

    @wraps(fn)
    def wrapped(key: str):
        color = fn(key)
        return color_from_tuple(color)

    return wrapped


def get_text_color(fn):
    fn.__annotations__ = {"key": str, "return": Annotated[TTextColors, Json]}

    @wraps(fn)
    def wrapped(key: str):
        colors = fn(key)
        return {
            "foreground": color_from_tuple(colors[0]),
            "background": color_from_tuple(colors[1], allow_turn_to_none=True),
        }

    return wrapped


def set_text_color(fn):
    fn.__annotations__ = {"key": str, "colors": Annotated[TTextColors, Json]}

    @wraps(fn)
    def wrapped(key: str, colors: Annotated[TTextColors, Json]):
        return fn(key, text_colors_to_tuple(colors))

    return wrapped


def get_data_from_box(
    box: Box, key, is_list=False
) -> Union[bytes, FileHandle, List[bytes], List[FileHandle]]:
    data_key = f"{key}_data"
    file_key = f'{key}_file{"s" if is_list else ""}'
    if data_key in box and (data := box[data_key]):
        return base64.b64decode(data)
    elif file_key in box:
        if is_list:
            return [
                FileHandle(file)
                for file in extension_manager.organize_paths(box[file_key])
            ]
        return FileHandle(extension_manager.organize_path(box[file_key]))
    raise ValueError(f"No {key} data found in {box}")


def make_task_id() -> int:
    """
    Generates a random 64bit unsigned integer to be used as a task id in extension callbacks.
    :return: random task id
    """
    return random.getrandbits(64)
