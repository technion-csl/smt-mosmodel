import pandas as pd
import os


class Configuration:
    TYPE = "type"
    PAGE_SIZE = "pageSize"
    START_OFFSET = "startOffset"
    END_OFFSET = "endOffset"
    TYPE_FILE = "file"
    TYPE_MMAP = "mmap"
    TYPE_BRK = "brk"
    POOL_SIZE_FLAG = -1
    LAYOUT_DIRECTORY = "layouts"

    def __init__(self, abs_path, layout_name):
        self.config = []
        self.layout_name = layout_name
        path = os.path.join(abs_path, Configuration.LAYOUT_DIRECTORY)
        if not os.path.exists(path):
            os.makedirs(path)
        self.export_file_name = os.path.join(path, layout_name + ".csv")

    def addWindow(self, type, page_size, start_offset, end_offset):
        row = {
            self.END_OFFSET: end_offset,
            self.START_OFFSET: start_offset,
            self.PAGE_SIZE: page_size,
            self.TYPE: type

        }
        self.config.append(row)

    def setPoolsSize(self, brk_size, file_size, mmap_size):
        if brk_size is not None:
            self.addWindow(
                type=Configuration.TYPE_BRK, page_size=self.POOL_SIZE_FLAG, start_offset=0, end_offset=brk_size)
        if file_size is not None:
            self.addWindow(type=self.TYPE_FILE,
                           page_size=self.POOL_SIZE_FLAG, start_offset=0, end_offset=file_size)
        if mmap_size is not None:
            self.addWindow(type=self.TYPE_MMAP,
                           page_size=self.POOL_SIZE_FLAG, start_offset=0, end_offset=mmap_size)

    def exportToCSV(self):
        df = pd.DataFrame(self.config, index=None)
        # rearrange columns
        df = df[[Configuration.TYPE, Configuration.PAGE_SIZE,
                 Configuration.START_OFFSET, Configuration.END_OFFSET]]
        df.to_csv(self.export_file_name, index=None)


# from utils import *
# path = os.path.dirname(__file__)
# data = Configuration(path, "layout1")


# data.setPoolsSize(gb, mb*2, mb*100)
# data.addWindow(Configuration.TYPE_BRK, gb, 0, gb)
# data.exportToCSV()
# data = Configuration(path, "layout2")


# data.setPoolsSize(gb, mb*2, mb*100)
# data.addWindow(Configuration.TYPE_BRK, gb, 0, gb)
# data.exportToCSV()