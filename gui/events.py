from typing import List, Union, Optional

from rm_api import DocumentCollection, Document
from rm_api.notifications.models import Notification


class BaseDocumentsNotification(Notification):
    def __init__(self, documents: List[str]):
        self.documents = documents


class BaseItemNotification(Notification):
    def __init__(self, uuid: str):
        self.uuid = uuid


class BaseItemsNotification(Notification):
    def __init__(self, items: List[Union[Document, DocumentCollection]]):
        self.documents = []
        self.collections = []
        for item in items:
            if isinstance(item, Document):
                self.documents.append(item.uuid)
            elif isinstance(item, DocumentCollection):
                self.collections.append(item.uuid)
            else:
                raise TypeError(f"Item must be a Document or DocumentCollection, got {type(item)}")


class BaseNameFieldCompleteNotification(Notification):
    def __init__(self, name: str):
        self.name = name


class ResizeEvent(Notification):
    def __init__(self, new_size):
        self.new_size = new_size


class MossFatal(Notification):
    """
        This signals the code should stop execution instantly
    """
    ...


class ScreenClosure(Notification):
    """
        This signals that a screen has just been closed by the Moss GUI
    """

    def __init__(self, screen_id: int, screen_class: str):
        self.screen_id = screen_id
        self.screen_class = screen_class


# Import screen

class ScreenIdentifiedDocumentsNotification(BaseDocumentsNotification):
    def __init__(self, documents: List[str], screen_id: int):
        super().__init__(documents)
        self.screen_id = screen_id


class ImportScreenLightSyncInit(ScreenIdentifiedDocumentsNotification):
    """
        This signals that a light sync operation was initiated within the import screen
    """
    ...


class ImportScreenLightSyncComplete(ScreenIdentifiedDocumentsNotification):
    """
        This signals that a light sync operation was completed within the import screen
    """
    ...


class ImportScreenFullSyncConfirm(ScreenIdentifiedDocumentsNotification):
    """
        This signals that a full sync operation was initiated and the import screen was dismissed
    """
    ...


# Main menu screen

class BaseNamedItem(BaseNameFieldCompleteNotification):
    def __init__(self, name: str, uuid: str):
        super().__init__(name)
        self.uuid = uuid


class BaseRenamedItem(BaseNamedItem):
    def __init__(self, name: str, uuid: str, old_name: str):
        super().__init__(name, uuid)
        self.old_name = old_name


class CreateNotebookInit(Notification):
    """
        This signals that a notebook creation prompt was initiated
    """


class CreateNotebookCancelled(Notification):
    """
        This signals that a notebook creation prompt was cancelled
    """


class CreateNotebookConfirmed(BaseNamedItem):
    """
        This signals that a notebook creation prompt was confirmed
    """


class CreateCollectionInit(Notification):
    """
        This signals that a collection creation prompt was initiated
    """


class CreateCollectionCancelled(Notification):
    """
        This signals that a collection creation prompt was cancelled
    """


class CreateCollectionConfirmed(BaseNamedItem):
    """
        This signals that a collection creation prompt was confirmed
    """


class UserDeleteInit(BaseItemsNotification):
    """
        This signals that a user delete operation was initiated
        NOTE: the items here are only the top level items selected by the user,
        does not include the children of collections
    """


class UserDeleteConfirmed(BaseItemsNotification):
    """
        This signals that a user delete operation was confirmed
        NOTE: the items here are all the items that will be deleted,
        including the children of collections that the user selected
    """


class UserDeleteCancelled(Notification):
    """
        This signals that a user delete operation was cancelled
    """


class UserDuplicateConfirmed(BaseItemsNotification):
    """
        This signals that a user duplicate operation was confirmed
        NOTE: the items here are all the items that will are duplicated and their originals,
        including the children of collections that the user selected
    """

    def __init__(self, items: List[Union[Document, DocumentCollection]],
                 duplicated_items: List[Union[Document, DocumentCollection]]):
        super().__init__(items)
        self.duplicated_documents = []
        self.duplicated_collections = []
        for item in duplicated_items:
            if isinstance(item, Document):
                self.duplicated_documents.append(item.uuid)
            elif isinstance(item, DocumentCollection):
                self.duplicated_collections.append(item.uuid)
            else:
                raise TypeError(f"Item must be a Document or DocumentCollection, got {type(item)}")


class UserFavoritesConfirmed(BaseItemsNotification):
    """
        This signals that a user confirmed a favorite operation
        NOTE: the items here are all the items that will be favorite,
        only the top level items selected by the user
    """


class RenameNotebookInit(BaseItemNotification):
    """
        This signals that a notebook rename prompt was initiated
    """


class RenameNotebookCancelled(BaseItemNotification):
    """
        This signals that a notebook rename prompt was cancelled
    """


class RenameNotebookConfirmed(BaseRenamedItem):
    """
        This signals that a notebook rename prompt was confirmed
    """


class RenameCollectionInit(BaseItemNotification):
    """
        This signals that a collection rename prompt was initiated
    """


class RenameCollectionCancelled(BaseItemNotification):
    """
        This signals that a collection rename prompt was cancelled
    """


class RenameCollectionConfirmed(BaseRenamedItem):
    """
        This signals that a collection rename prompt was confirmed
    """


class MoveConfirmed(BaseItemsNotification):
    """
        This signals that a user move operation was confirmed
        NOTE: the items here are all the items that will be moved,
        including the children of collections that the user selected
    """

    def __init__(self, items: List[Union[Document, DocumentCollection]],
                 new_parent: Optional[str]):
        super().__init__(items)
        self.new_parent = new_parent
