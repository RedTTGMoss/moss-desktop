from functools import wraps
from typing import TypedDict, Type, get_origin, Annotated, List

from box import Box
from extism import Json

from .accessor_handlers import (
    document_inferred,
    file_sync_progress_inferred,
    event_inferred,
)
from .shared_types import AccessorInstance


def check_ref(func):
    """
    Check if the function accepts a reference to the document or collection.
    """
    has_ref = "ref" in func.__annotations__
    if has_ref:
        func.__annotations__.pop("ref")
    return has_ref


def accept_change_accessor_field(default_accessor_field):
    def wrapper(fn):  # Make a wrapper with the default accessor field
        # Change the wrapped wrapper to add an accessor field
        def field_change(accessor=default_accessor_field):
            # Finally wrap the wrapper to add the accessor field
            @wraps(fn)
            def wrapped(*args, **kwargs):
                return fn(accessor, *args, **kwargs)

            return wrapped  # Return the wrapped wrapper

        return field_change  # Return the wrapper wrapper

    return wrapper  # Return the wrapper wrapper accessor function


def blank_ref_wrapper(item_type):
    def wrapper(func):
        @wraps(func)
        def wrapped(item: item_type, *args, **kwargs):
            return func(item, *args, **kwargs)

        return wrapped

    return wrapper


def check_is_dict(_t: Type[TypedDict]):
    return isinstance(_t, type) and issubclass(_t, dict) or get_origin(_t) is dict


@accept_change_accessor_field("accessor")
def document_wrapper(accessor_field, func):
    """
    This wrapper is for documents.
    Takes in accessor.
    """
    func.__annotations__.pop("item")
    needs_accessor = accessor_field in func.__annotations__
    if needs_accessor:
        func.__annotations__.pop(accessor_field)
    func.__annotations__ = {
        accessor_field: Annotated[AccessorInstance, Json],
        **func.__annotations__,
    }

    @wraps(func)
    def wrapper(accessor: Annotated[AccessorInstance, Json], *args, **kwargs):
        document, _ = document_inferred(box := Box(accessor))
        if needs_accessor:
            kwargs[accessor_field] = box
        return func(document, *args, **kwargs)

    return wrapper


@accept_change_accessor_field("accessors")
def many_document_wrapper(accessor_field, func):
    """
    This wrapper is for documents.
    Takes in accessors.
    """
    func.__annotations__.pop("items")
    needs_accessors = accessor_field in func.__annotations__
    if needs_accessors:
        func.__annotations__.pop(accessor_field)
    func.__annotations__ = {
        accessor_field: Annotated[List[AccessorInstance], Json],
        **func.__annotations__,
    }

    @wraps(func)
    def wrapper(accessors: Annotated[List[AccessorInstance], Json], *args, **kwargs):
        boxes = [Box(accessor) for accessor in accessors]
        documents = [document_inferred(accessor)[0] for accessor in boxes]
        if needs_accessors:
            kwargs[accessor_field] = boxes
        return func(documents, *args, **kwargs)

    return wrapper


@accept_change_accessor_field("accessor")
def file_sync_progress_wrapper(accessor_field, func):
    """
    This wrapper is for FileSyncProgress.
    Takes in accessor.
    """
    func.__annotations__.pop("item")
    needs_accessor = accessor_field in func.__annotations__
    if needs_accessor:
        func.__annotations__.pop(accessor_field)
    func.__annotations__ = {
        accessor_field: Annotated[AccessorInstance, Json],
        **func.__annotations__,
    }

    @wraps(func)
    def wrapper(accessor: Annotated[AccessorInstance, Json], *args, **kwargs):
        document, _ = file_sync_progress_inferred(box := Box(accessor))
        if needs_accessor:
            kwargs[accessor_field] = box
        return func(document, *args, **kwargs)

    return wrapper


@accept_change_accessor_field("accessor")
def event_wrapper(accessor_field, func):
    """
    This wrapper is for API notifactions / events
    Takes in accessor.
    """
    func.__annotations__.pop("item")
    needs_accessor = accessor_field in func.__annotations__
    if needs_accessor:
        func.__annotations__.pop(accessor_field)
    func.__annotations__ = {
        accessor_field: Annotated[AccessorInstance, Json],
        **func.__annotations__,
    }

    @wraps(func)
    def wrapper(accessor: Annotated[AccessorInstance, Json], *args, **kwargs):
        document, _ = event_inferred(box := Box(accessor))
        if needs_accessor:
            kwargs[accessor_field] = box
        return func(document, *args, **kwargs)

    return wrapper
