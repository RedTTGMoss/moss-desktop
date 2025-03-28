from typing import Iterator
from uuid import uuid4, UUID

from ..rmscene import SceneGroupItemBlock, CrdtId, LwwValue, TreeNodeBlock, SceneTreeBlock, PageInfoBlock, \
    MigrationInfoBlock, AuthorIdsBlock, Block
from ..rmscene import scene_items as si
from ..rmscene.crdt_sequence import CrdtSequenceItem


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
