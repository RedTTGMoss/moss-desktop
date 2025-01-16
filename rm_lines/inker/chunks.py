import pygameextra as pe
from rmscene import SceneTree


class rM_Chunks:
    def __init__(self, tree: SceneTree):
        self.tree = tree
        self.pnzc = pe.PanAndZoomChunks(
            self.get
        )

    def get(self, x, y):
        pass
