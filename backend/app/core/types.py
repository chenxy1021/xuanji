"""跨领域共用的数据结构：生辰输入、排盘信封。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

CalendarType = Literal["solar", "lunar"]
Gender = Literal["male", "female"]
Shichen = Literal["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

SHICHEN_HOURS: dict[str, tuple[int, int]] = {
    "子": (23, 1),
    "丑": (1, 3),
    "寅": (3, 5),
    "卯": (5, 7),
    "辰": (7, 9),
    "巳": (9, 11),
    "午": (11, 13),
    "未": (13, 15),
    "申": (15, 17),
    "酉": (17, 19),
    "戌": (19, 21),
    "亥": (21, 23),
}


class Place(BaseModel):
    """出生地：用于真太阳时校正与星盘计算。

    `timezone` 是当地**标准时**相对 UTC 的小时偏移（东正西负，-12..14），
    排盘只用它推标准子午线与换算 UTC，不处理夏令时。
    """

    name: str = ""
    province: str = ""
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    timezone: float = Field(default=8.0, ge=-12, le=14)


class BirthInput(BaseModel):
    """统一生辰模型，所有体系共用。"""

    calendar: CalendarType = "solar"
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    shichen: Shichen | None = None
    is_leap_month: bool = False
    gender: Gender = "male"
    true_solar_time: bool = True
    place: Place | None = None

    @field_validator("minute")
    @classmethod
    def _default_minute(cls, v: int | None, info) -> int | None:
        if v is None and info.data.get("hour") is not None:
            return 0
        return v

    @property
    def has_exact_time(self) -> bool:
        return self.hour is not None

    def resolved_hour_minute(self) -> tuple[int | None, int | None]:
        """返回 (hour, minute)；未给精确时刻时按地支时辰取中点。"""
        if self.hour is not None:
            return self.hour, self.minute or 0
        if self.shichen:
            start, end = SHICHEN_HOURS[self.shichen]
            if self.shichen == "子":
                return 0, 0
            return (start + end) // 2, 0
        return None, None


class ChartEnvelope(BaseModel):
    """所有体系排盘响应的统一信封。"""

    system: str
    engine_version: str = "0.1.0"
    input: dict[str, Any]
    chart: dict[str, Any]
    text: str
    warnings: list[str] = Field(default_factory=list)


class ChartRequest(BaseModel):
    birth: BirthInput | None = None
    """第二个人（合盘类体系使用）。"""
    secondary: BirthInput | None = None
    options: dict[str, Any] = Field(default_factory=dict)


SystemCategory = Literal["chart", "synastry", "divination", "fortune", "fun"]


class OptionField(BaseModel):
    """非生辰类体系的通用表单字段，前端据此渲染输入控件。

    *_en 为中英切换用的英文文案：没有翻译就留 None（不要留空串），
    前端在缺英文时自动回退到中文字段。
    """

    key: str
    label: str
    kind: Literal["select", "number", "text", "textarea", "date", "time", "datetime", "toggle"] = "text"
    required: bool = False
    default: Any = None
    options: list[dict[str, str]] | None = None
    placeholder: str = ""
    hint: str = ""
    label_en: str | None = None
    placeholder_en: str | None = None
    hint_en: str | None = None


class SystemSpec(BaseModel):
    id: str
    name: str
    tagline: str
    requires_birth: bool = True
    requires_time: bool = True
    requires_secondary: bool = False
    category: SystemCategory = "chart"
    fields: list[OptionField] = Field(default_factory=list)
    status: Literal["ready", "beta", "planned"] = "beta"
    name_en: str | None = None
    tagline_en: str | None = None
