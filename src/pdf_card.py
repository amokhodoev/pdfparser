import re
from configparser import ConfigParser
from datetime import datetime
from typing import List, Union, Optional

from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

from src.barcode import BarCode
from src.model import PdfCardModel

config = ConfigParser()
config.read("./config.ini")
poppler_path = config.get("GENERAL", "poppler_path")


class PdfCard:

    def __init__(self, path: str, fields_map, fields_order):
        self.file_path = path
        self.fields_map = fields_map
        self.fields_order = fields_order

        self._reader = PdfReader(path)
        self.page = self._reader.pages[0]
        self.image_pdf: Image = self._pdf_to_image()
        self._text: str = self.page.extract_text()
        self.kwargs = dict()
        self._process_fields()
        self.check_order()
        self.kwargs['top_bar_code'] = self._find_bar_code(58, 731)
        self.kwargs['tagged_by'] = self._find_bar_code(83, 192)
        self.model = None

    def validate(self):
        """validate fields of pdf doc"""

        self.model = PdfCardModel(**self.kwargs)

    def check_order(self):
        """Checking if order is matching to expected"""

        text_order = re.findall('|'.join(self.fields_order), self._text)
        assert text_order == self.fields_order, "Wrong order"

    def _process_fields(self):
        """Going through the text and filling dict of fields"""

        self.kwargs['label'] = self._text.split('\n')[0]
        for field_type, fields in self.fields_map.items():
            for field in fields:
                field_name = field.lower().replace("#", "").replace(" ", "_").replace(".", "_")
                field_value = None
                if field_type == 'str_fields':
                    field_value = re.search(field + r" ?:\s(\w+)", self._text).group(1)
                elif field_type == 'int_fields':
                    field_value = re.search(field + r" ?:\s(\d+)", self._text).group(1)
                    field_value = int(field_value)
                elif field_type == 'date_fields':
                    field_value = re.search(field + r" ?:\s(\d{2}\.\d{2}.\d{4})", self._text).group(1)
                    field_value = datetime.strptime(field_value, "%d.%m.%Y")
                elif field_type == 'list_fields':
                    field_value = re.search(field + r" ?:((\n\w+)+)(\n\w+ ?:\s\w+)?", self._text).group(1)
                    field_value = field_value.split('\n')
                self.kwargs[field_name] = field_value

    def _pdf_to_image(self) -> Image:
        """
        Convert PDF file to image
        :return: Pillow Image
        """

        images_from_path = convert_from_path(self.file_path, poppler_path=poppler_path)

        return images_from_path[0]

    @staticmethod
    def __divide_on_intervals(digits: List[int], max_width: int) -> List[List[int]]:
        """divide pixels list for an intervals
        :param digits: list of sorted digits
        :param max_width: width
        :return: list of intervals
        """

        if not digits:
            return []
        intervals = []
        tmp = [x for x in digits if x <= digits[0] + max_width]
        if abs(tmp[-1] - tmp[0] - max_width) > 1:
            return []
        current_range = [digits[0]]
        for i in range(1, len(tmp)):
            if tmp[i] - tmp[i - 1] != 1:
                current_range.append(tmp[i - 1])
                intervals.append(current_range)
                current_range = [tmp[i]]
        else:
            current_range.append(tmp[-1])
            intervals.append(current_range)

        return intervals

    def __check_is_bar(self, interval: List[int], height: int, y: int) -> Union[bool, int]:
        """Check if current interval is bar of barcode with desirable height
        :param interval:
        :param height: expected height of bar
        :param y: coordinate of bar
        """
        for _x in range(interval[0], interval[1] + 1):
            for _y in range(height):
                if self.image_pdf.getpixel((_x, y + _y)) == (255, 255, 255):
                    return _y + 1
        return True

    def _find_bar_code(self, height: int, width: int) -> Optional[BarCode]:
        """Find the bar code on the image with given height and width of barcode.
        :param height: height of barcode
        :param width: width of barcode
        """

        # Processing image
        for y in range(self.image_pdf.height):
            black_pixels = []
            for x in range(self.image_pdf.width):
                pixel = self.image_pdf.getpixel((x, y))

                if pixel != (255, 255, 255):
                    black_pixels.append(x)

            # divide pixels list for an intervals
            intervals = self.__divide_on_intervals(black_pixels, width)
            if intervals:
                for interval in intervals:
                    is_bar = self.__check_is_bar(interval, height, y)
                    if is_bar is not True:
                        # as it's not the barcode going down to the latest found white pixel
                        y += is_bar
                        break
                else:
                    # BarCode found
                    start_x = intervals[0][0]
                    bars = [list(map(lambda item: item - start_x, interval)) for interval in intervals]
                    return BarCode(height, width, *bars)

        return None
