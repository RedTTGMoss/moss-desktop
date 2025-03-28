from io import BytesIO, StringIO
from pprint import pprint
from typing import TYPE_CHECKING, Tuple

from rm_lines.inker.document_size_tracker import DocumentSizeTracker
# RM_LINES
from .inker import tree_to_svg
from .rmscene import read_tree, SceneGroupItemBlock, CrdtId, LwwValue, TreeNodeBlock, SceneTreeBlock, PageInfoBlock, \
    MigrationInfoBlock, AuthorIdsBlock, Block, write_blocks
from .rmscene import scene_items as si
from .rmscene.crdt_sequence import CrdtSequence, CrdtSequenceItem
from .writer import blank_document

if TYPE_CHECKING:
    from rm_api import Document


def get_children(sequence: CrdtSequence):
    return [
        get_children(child) if getattr(child, 'children', None) else child
        for child in map(lambda child_id: sequence.children[child_id], sequence.children)
    ]


def rm_bytes_to_svg(data: bytes, document: 'Document', template: str = None, debug: bool = False) -> Tuple[
    str, DocumentSizeTracker]:
    tree = read_tree(BytesIO(data))

    if debug:
        print("RM file tree: ", end='')
        pprint(get_children(tree.root))

    track_xy = DocumentSizeTracker.create_from_document(document)

    with StringIO() as f:
        tree_to_svg(tree, f, track_xy, template)
        return f.getvalue(), track_xy


__all__ = ['read_tree', 'tree_to_svg', 'write_blocks', 'blank_document']
