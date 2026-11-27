"""跨领域共用的数据结构：生辰输入、排盘信封。

技能版用标准库 dataclass，不引入 pydantic；保留引擎需要的
model_validate / model_dump 两个接口，字段与校验行为不变。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Literal

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

SystemCategory = Literal["chart", "synastry", "divination", "fortune", "fun"]


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _jsonable(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


class _Model:
    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        return _jsonable(self)

    @classmethod
    def model_validate(cls, data: Any):
        if isinstance(data, cls):
            return data
        if isinstance(data, _Model):
            data = data.model_dump()
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__} 需要字典输入")
        return cls(**data)


def _check(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


@dataclass
class Place(_Model):
    """出生地：用于真太阳时校正与星盘计算。"""

    longitude: float
    latitude: float
    name: str = ""
    province: str = ""
    timezone: float = 8.0

    def __post_init__(self) -> None:
        _check(-180 <= self.longitude <= 180, "经度需在 -180..180")
        _check(-90 <= self.latitude <= 90, "纬度需在 -90..90")
        _check(-12 <= self.timezone <= 14, "时区需在 -12..14")


@dataclass
class BirthInput(_Model):
    """统一生辰模型，所有体系共用。"""

    year: int
    month: int
    day: int
    calendar: CalendarType = "solar"
    hour: int | None = None
    minute: int | None = None
    shichen: Shichen | None = None
    is_leap_month: bool = False
    gender: Gender = "male"
    true_solar_time: bool = True
    place: Place | dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _check(self.calendar in ("solar", "lunar"), "历法只能是 solar 或 lunar")
        _check(self.gender in ("male", "female"), "性别只能是 male 或 female")
        _check(1900 <= self.year <= 2100, "年份需在 1900-2100")
        _check(1 <= self.month <= 12, "月份需在 1-12")
        _check(1 <= self.day <= 31, "日期需在 1-31")
        if self.hour is not None:
            _check(0 <= self.hour <= 23, "小时需在 0-23")
            if self.minute is None:
                self.minute = 0
        if self.minute is not None:
            _check(0 <= self.minute <= 59, "分钟需在 0-59")
        if self.shichen is not None:
            _check(self.shichen in SHICHEN_HOURS, "时辰需为十二地支之一")
        if isinstance(self.place, dict):
            self.place = Place(**self.place)

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


@dataclass
class ChartEnvelope(_Model):
    """所有体系排盘响应的统一信封。"""

    system: str
    input: dict[str, Any]
    chart: dict[str, Any]
    text: str
    engine_version: str = "0.1.0"
    warnings: list[str] = field(default_factory=list)


@dataclass
class ChartRequest(_Model):
    birth: BirthInput | None = None
    """第二个人（合盘类体系使用）。"""
    secondary: BirthInput | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptionField(_Model):
    """非生辰类体系的表单字段。"""

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


@dataclass
class SystemSpec(_Model):
    id: str
    name: str
    tagline: str
    requires_birth: bool = True
    requires_time: bool = True
    requires_secondary: bool = False
    category: SystemCategory = "chart"
    fields: list[OptionField] = field(default_factory=list)
    status: Literal["ready", "beta", "planned"] = "beta"
    name_en: str | None = None
    tagline_en: str | None = None
