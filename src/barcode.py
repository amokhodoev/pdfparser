"""Barcode object"""


class BarCode:

    def __init__(self, height, width, *bars):
        self.height = height
        self.width = width
        self.bars = bars

    def is_valid(self, min_bar_width: int, bar_len: int) -> bool:
        """Check if barcode is valid"""

        if len(self.bars) != bar_len:
            return False

        return all(map(lambda x: x[1] - x[0] >= min_bar_width, self.bars))
