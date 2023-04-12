from datetime import datetime
from typing import List

from pydantic import BaseModel, validator

from .barcode import BarCode

from configparser import ConfigParser

config = ConfigParser()
config.read("../config.ini")


class PdfCardModel(BaseModel):
    label: str
    top_bar_code: BarCode
    pn: str
    description: str
    receiver: int
    exp_date: datetime
    cert_source: str
    rec_date: datetime
    batch: int
    remark: str
    tagged_by: BarCode
    qty: int
    sn: int
    condition: str
    uom: str
    po: str
    mfg: str
    dom: datetime
    lot: int
    notes: List[str]

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    @validator("top_bar_code")
    def validate_barcode(cls, value):
        min_bar_size = config.get("GENERAL", "MIN_BAR_SIZE")
        barcode_len = config.get("GENERAL", "BARCODE_LENGTH")
        return value.is_valid(min_bar_size, barcode_len)

    @classmethod
    @validator("tagged_by")
    def validate_tagged_by_barcode(cls, value):
        min_bar_size = config.get("GENERAL", "MIN_TAGGED_BAR_SIZE")
        barcode_len = config.get("GENERAL", "TAGGED_BARCODE_LENGTH")
        return value.is_valid(min_bar_size, barcode_len)
