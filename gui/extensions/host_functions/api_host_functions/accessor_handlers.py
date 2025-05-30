from functools import partial
from typing import Tuple, Union, Optional

from gui.events import MossFatal
from gui.i10n import t
from gui.sync_stages import SYNC_STAGE_TEXTS, SYNC_STAGE_ICONS
from rm_api import DocumentCollection, Document, Metadata, APIFatal
from .shared_types import AccessorInstanceBox, AccessorTypes
from .. import definitions as d


class SyncExtensionFunctionHelper:
    """
        Custom Moss extension accessor for sync stages.
    """

    def __init__(self, accessor):
        self.accessor = accessor
        self.extension = d.extension_manager.current_extension_index

    def add_accessor(self, dictionary):
        pass  # The accessor is already added to the dictionary

    @staticmethod
    def get_index(accessor_index, extension_index):
        index = accessor_index
        if index > 999:
            raise IndexError("Your extension cannot set custom sync stages above 999.")
        if index > 99:
            index = extension_index * 1000 + (index - 99)
        return index

    @property
    def index(self):
        return self.get_index(self.accessor['id'], self.extension)

    def __dict__(self):
        return {
            'text': self.text,
            'icon': self.icon,
            'accessor': self.accessor
        }

    @property
    def text(self):
        return t(SYNC_STAGE_TEXTS[self.index])

    @text.setter
    def text(self, text):
        SYNC_STAGE_TEXTS[self.index] = text
        text_key = f'rm_api_stage_{self.index}'
        if text_obj := d.gui.main_menu.texts.get(text_key):
            text_obj.text = text
            text_obj.init()
        else:
            d.gui.main_menu.__class__.SMALL_HEADER_TEXTS[text_key] = text
            d.gui.main_menu.make_small_header_text(text_key, text)

    @property
    def icon(self):
        return SYNC_STAGE_ICONS[self.index]

    @icon.setter
    def icon(self, icon):
        SYNC_STAGE_ICONS[self.index] = icon

    @classmethod
    def set_stage(cls, obj, _, value):
        index = cls.get_index(value, d.extension_manager.current_extension_index)
        setattr(obj, 'stage', index)


def uuid_accessor_adder(accessor_type: str, dictionary: dict):
    """
        This function adds the accessor to the API/Standalone document and collection objects.
        :param accessor_type: The accessor string
        :param dictionary: The dictionary to add the accessor to
    """
    dictionary['accessor'] = {
        'type': accessor_type,
        'uuid': dictionary['uuid']
    }
    if metadata := dictionary.get('metadata'):
        metadata['accessor'] = {
            'type': f'{accessor_type}_metadata',
            'uuid': dictionary['uuid']
        }
    if content := dictionary.get('content'):
        content['accessor'] = {
            'type': f'{accessor_type}_content',
            'uuid': dictionary['uuid']
        }


def parent_accessor_adder(accessor_type: str, parent: Optional[Union[Document, DocumentCollection]], dictionary: dict,
                          object_id: int = None):
    """
        This function adds the accessor to the metadata and content objects.
        :param accessor_type: The accessor string
        :param parent: An optional parent document or collection object, if the object is not standalone
        :param dictionary: The dictionary to add the accessor to
        :param object_id: An optional object id, if the object is standalone
    """
    dictionary['accessor'] = {
        'type': accessor_type,
    }
    if parent:
        dictionary['accessor']['uuid'] = parent.uuid
    else:
        dictionary['accessor']['id'] = object_id


def document_inferred(accessor: AccessorInstanceBox) -> Tuple[Document, partial]:
    """
        Infer the document object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The document object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APIDocument: lambda _: (d.api.documents[_.uuid], partial(uuid_accessor_adder, _.type)),
        AccessorTypes.StandaloneDocument: lambda _: (
            d.extension_manager.document_objects[_.uuid], partial(uuid_accessor_adder, _.type)),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for document inferring")


def collection_inferred(accessor: AccessorInstanceBox) -> Tuple[DocumentCollection, partial]:
    """
        Infer the collection object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The collection object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APICollection: lambda _: (
            d.api.document_collections[_.uuid], partial(uuid_accessor_adder, _.type)),

        AccessorTypes.StandaloneCollection: lambda _: (
            d.extension_manager.collection_objects[_.uuid], partial(uuid_accessor_adder, _.type)),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for collection inferring")


def metadata_inferred(accessor: AccessorInstanceBox) -> Tuple[Metadata, partial]:
    """
        Infer the metadata object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The metadata object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APIDocumentMetadata: lambda _: (
            (parent := d.api.documents[_.uuid]).metadata, partial(parent_accessor_adder, _.type, parent)),
        AccessorTypes.APICollectionMetadata: lambda _: (
            (parent := d.api.document_collections[_.uuid]).metadata, partial(parent_accessor_adder, _.type, parent)),

        AccessorTypes.StandaloneDocumentMetadata: lambda _: (
            (parent := d.extension_manager.document_objects[_.uuid]).metadata,
            partial(parent_accessor_adder, _.type, parent)),
        AccessorTypes.StandaloneCollectionMetadata: lambda _: (
            (parent := d.extension_manager.collection_objects[_.uuid]).metadata,
            partial(parent_accessor_adder, _.type, parent)),

        AccessorTypes.StandaloneMetadata: lambda _: (
            obj := d.extension_manager.metadata_objects[_.id],
            partial(parent_accessor_adder, _.type, None, object_id=id(obj))),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for metadata inferring")


def content_inferred(accessor: AccessorInstanceBox):
    """
        Infer the content object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The content object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.APIDocumentContent: lambda _: (
            (parent := d.api.documents[_.uuid]).content, partial(parent_accessor_adder, _.type, parent)),
        AccessorTypes.StandaloneDocumentContent: lambda _: (
            (parent := d.extension_manager.document_objects[_.uuid]).content,
            partial(parent_accessor_adder, _.type, parent)),

        AccessorTypes.StandaloneContent: lambda _: (
            obj := d.extension_manager.content_objects[_.id],
            partial(parent_accessor_adder, _.type, None, object_id=id(obj))),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for content inferring")


def file_sync_progress_inferred(accessor: AccessorInstanceBox):
    """
        Infer the content object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The FileSyncProgres object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.FileSyncProgress: lambda _: (
            obj := d.extension_manager.file_sync_progress_objects[_.id],
            partial(parent_accessor_adder, _.type, None, object_id=id(obj))
        )
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for FileSyncProgres inferring")


def document_sync_progress_inferred(accessor: AccessorInstanceBox):
    """
        Infer the content object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The DocumentSyncProgres object and a function to add the accessor to the dictionary
    """
    getters = {
        AccessorTypes.DocumentSyncProgress: lambda _: (
            obj := d.extension_manager.document_sync_progress_objects[_.id],
            partial(parent_accessor_adder, _.type, None, object_id=id(obj))
        )
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for DocumentSyncProgres inferring")


def event_inferred(accessor: AccessorInstanceBox):
    """
        Infer the content object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The Event object and a no function
    """
    getters = {
        AccessorTypes.FileSyncProgress: lambda _: (d.extension_manager.file_sync_progress_objects[_.id], None),
        AccessorTypes.DocumentSyncProgress: lambda _: (d.extension_manager.document_sync_progress_objects[_.id], None),
        AccessorTypes.EventMossFatal: lambda _: (MossFatal(), None),
        AccessorTypes.EventApiFatal: lambda _: (APIFatal(), None),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for Event inferring")


def sync_stage_inferred(accessor: AccessorInstanceBox):
    """
        Infer the content object from the accessor instance.
        :param accessor: A box of the accessor instance
        :return: The sync stage setter handler
    """

    getters = {
        AccessorTypes.SyncStage: lambda _: (obj := SyncExtensionFunctionHelper(_), obj.add_accessor),
    }

    if (getter := getters.get(AccessorTypes(accessor.type))) is not None:
        return getter(accessor)
    else:
        raise NotImplementedError("This accessor type is not supported for Event inferring")
