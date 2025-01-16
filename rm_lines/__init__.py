from io import BytesIO, StringIO
from pprint import pprint
from typing import Iterator
from uuid import UUID, uuid4

from pygameextra import settings

from rm_lines.inker.document_size_tracker import DocumentSizeTracker
from .inker import tree_to_svg
from .rmscene import read_tree, SceneGroupItemBlock, CrdtId, LwwValue, TreeNodeBlock, SceneTreeBlock, PageInfoBlock, \
    MigrationInfoBlock, AuthorIdsBlock, Block, write_blocks
from .rmscene import scene_items as si
from .rmscene.crdt_sequence import CrdtSequence, CrdtSequenceItem


def get_children(sequence: CrdtSequence):
    return [
        get_children(child) if getattr(child, 'children', None) else child
        for child in map(lambda child_id: sequence.children[child_id], sequence.children)
    ]


def read_rm_bytes(data: bytes):
    tree = read_tree(BytesIO(data))

    if settings.config.debug_lines:
        print("RM file tree: ", end='')
        pprint(get_children(tree.root))

    return tree


def rm_bytes_to_svg(data: bytes, track_xy: DocumentSizeTracker = None):
    tree = read_tree(data)

    with StringIO() as f:
        tree_to_svg(tree, f, track_xy)
        return f.getvalue()


def rm_bytes_to_chunks(data: bytes, track_xy: DocumentSizeTracker = None):
    tree = read_tree(data)

    return


def blank_document(author_uuid=None) -> Iterator[Block]:
    """Return the blocks for a blank document
    """

    if author_uuid is None:
        author_uuid = uuid4()
    elif isinstance(author_uuid, str):
        author_uuid = UUID(author_uuid)

    yield AuthorIdsBlock(author_uuids={1: author_uuid})

    yield MigrationInfoBlock(migration_id=CrdtId(1, 1), is_device=True)

    yield PageInfoBlock(
        loads_count=1,
        merges_count=0,
        text_chars_count=0,
        text_lines_count=0
    )

    yield SceneTreeBlock(
        tree_id=CrdtId(0, 11),
        node_id=CrdtId(0, 0),
        is_update=True,
        parent_id=CrdtId(0, 1),
    )

    yield TreeNodeBlock(
        si.Group(
            node_id=CrdtId(0, 1),
        )
    )

    yield TreeNodeBlock(
        si.Group(
            node_id=CrdtId(0, 11),
            label=LwwValue(timestamp=CrdtId(0, 12), value="Layer 1"),
        )
    )

    yield SceneGroupItemBlock(
        parent_id=CrdtId(0, 1),
        item=CrdtSequenceItem(
            item_id=CrdtId(0, 13),
            left_id=CrdtId(0, 0),
            right_id=CrdtId(0, 0),
            deleted_length=0,
            value=CrdtId(0, 11),
        ),
    )


__all__ = ['read_tree', 'tree_to_svg', 'write_blocks', 'blank_document']
