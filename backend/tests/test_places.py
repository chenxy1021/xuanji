"""出生地：国外城市检索、任意经纬度与时区的排盘契约。"""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.domains.shared.cities import CITIES, find_city, search_cities
from app.domains.shared.solar_time import (
    solar_time_info,
    standard_meridian_for,
    timezone_label,
    to_true_solar_time,
)
from app.main import app

client = TestClient(app)

BEIJING_PLACE = {
    "name": "北京市",
    "province": "北京",
    "longitude": 116.4074,
    "latitude": 39.9042,
    "timezone": 8.0,
}
TOKYO_PLACE = {
    "name": "东京",
    "province": "日本",
    "longitude": 139.6917,
    "latitude": 35.6895,
    "timezone": 9.0,
}


def _birth(place: dict | None, hour: int = 9) -> dict:
    payload: dict = {
        "year": 1990,
        "month": 5,
        "day": 15,
        "hour": hour,
        "minute": 30,
        "gender": "male",
    }
    if place is not None:
        payload["place"] = place
    return payload


def test_china_cities_keep_utc8() -> None:
    assert search_cities("北京")[0].timezone == 8.0
    assert find_city("北京市").timezone == 8.0
    assert find_city("香港").timezone == 8.0


def test_foreign_cities_searchable_by_english_alias() -> None:
    tokyo = search_cities("Tokyo")[0]
    assert tokyo.name == "东京"
    assert tokyo.timezone == 9.0
    # 大小写不敏感
    assert search_cities("tOkYo")[0].name == "东京"
    assert search_cities("new york")[0].name == "纽约"
    assert search_cities("New York")[0].timezone == -5.0
    london = search_cities("London")[0]
    assert london.name == "伦敦"
    assert london.timezone == 0.0
    # 半小时时区也要能带出
    assert search_cities("Mumbai")[0].timezone == 5.5


def test_foreign_cities_searchable_by_chinese_name_and_country() -> None:
    assert search_cities("首尔")[0].timezone == 9.0
    assert search_cities("悉尼")[0].timezone == 10.0
    # 按国家检索
    names = {city.name for city in search_cities("美国")}
    assert {"纽约", "洛杉矶", "旧金山"} <= names


def test_city_table_is_large_enough_and_timezones_sane() -> None:
    assert len(CITIES) >= 90
    foreign = [city for city in CITIES if city.timezone != 8.0]
    assert len(foreign) >= 25
    for city in CITIES:
        assert -12 <= city.timezone <= 14
        assert -180 <= city.longitude <= 180
        assert -90 <= city.latitude <= 90
        assert city.name


def test_geo_endpoint_returns_timezone() -> None:
    body = client.get("/api/v1/geo/cities", params={"q": "Singa"}).json()
    assert body and body[0]["name"] == "新加坡"
    assert body[0]["timezone"] == 8.0
    assert {"longitude", "latitude", "province"} <= set(body[0])


def test_standard_meridian_follows_timezone() -> None:
    assert standard_meridian_for(8.0) == 120.0
    assert standard_meridian_for(9.0) == 135.0
    assert standard_meridian_for(0.0) == 0.0
    assert standard_meridian_for(-5.0) == -75.0
    assert standard_meridian_for(5.5) == 82.5


def test_timezone_label_format() -> None:
    assert timezone_label(8.0) == "UTC+8"
    assert timezone_label(-5.0) == "UTC-5"
    assert timezone_label(5.5) == "UTC+5:30"
    assert timezone_label(0.0) == "UTC+0"


def test_solar_time_info_accepts_standard_meridian() -> None:
    clock = datetime(1990, 5, 15, 9, 30)
    info_default = solar_time_info(clock, 139.6917)
    assert info_default["standard_meridian"] == 120.0
    info_tokyo = solar_time_info(clock, 139.6917, standard_meridian_for(9.0))
    assert info_tokyo["standard_meridian"] == 135.0
    # 原有字段保持不变
    assert {"clock_time", "longitude_correction_minutes", "equation_of_time_minutes",
            "total_correction_minutes", "true_solar_time"} <= set(info_tokyo)
    # 基准子午线东移 15°，经度差修正少 60 分钟
    assert round(
        info_default["longitude_correction_minutes"] - info_tokyo["longitude_correction_minutes"], 2
    ) == 60.0
    # 同一时刻、同一经度，基准子午线东移 15° 后真太阳时早整 1 小时
    delta = to_true_solar_time(clock, 139.6917) - to_true_solar_time(clock, 139.6917, 135.0)
    assert delta.total_seconds() == 3600


def test_bazi_accepts_arbitrary_place_with_timezone() -> None:
    resp = client.post(
        "/api/v1/charts/bazi",
        json={"birth": _birth({"name": "自定义", "longitude": 139.6917,
                               "latitude": 35.6895, "timezone": 9.0})},
    )
    assert resp.status_code == 200, resp.text
    warnings = " ".join(resp.json().get("warnings") or [])
    assert "UTC+9" in warnings
    assert "135.0" in warnings


def test_bazi_tokyo_warning_mentions_local_timezone() -> None:
    resp = client.post("/api/v1/charts/bazi", json={"birth": _birth(TOKYO_PLACE)})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    warnings = " ".join(body.get("warnings") or [])
    assert "UTC+9" in warnings
    # 北京时间同一时刻的校正基准仍是 120°
    beijing = client.post("/api/v1/charts/bazi", json={"birth": _birth(BEIJING_PLACE)})
    assert beijing.status_code == 200
    assert "UTC+9" not in " ".join(beijing.json().get("warnings") or [])


def test_ziwei_uses_place_timezone() -> None:
    resp = client.post("/api/v1/charts/ziwei", json={"birth": _birth(TOKYO_PLACE)})
    assert resp.status_code == 200, resp.text
    warnings = " ".join(resp.json().get("warnings") or [])
    assert "UTC+9" in warnings

    beijing = client.post("/api/v1/charts/ziwei", json={"birth": _birth(BEIJING_PLACE)})
    assert beijing.status_code == 200, beijing.text
    assert "UTC+9" not in " ".join(beijing.json().get("warnings") or [])


def test_astrology_accepts_foreign_place() -> None:
    resp = client.post("/api/v1/charts/astrology", json={"birth": _birth(TOKYO_PLACE)})
    assert resp.status_code == 200, resp.text
    chart = resp.json()["chart"]
    assert chart["planets"], "星盘应返回行星"
    assert chart.get("rising") is not None, "有经纬度时应能算出上升"


def test_invalid_timezone_and_coordinates_are_rejected() -> None:
    bad_tz = client.post(
        "/api/v1/charts/bazi",
        json={"birth": _birth({"name": "x", "longitude": 0, "latitude": 0, "timezone": 20.0})},
    )
    assert bad_tz.status_code == 422, bad_tz.text
    bad_lat = client.post(
        "/api/v1/charts/bazi",
        json={"birth": _birth({"name": "x", "longitude": 0, "latitude": 91.0, "timezone": 8.0})},
    )
    assert bad_lat.status_code == 422, bad_lat.text
    bad_lon = client.post(
        "/api/v1/charts/bazi",
        json={"birth": _birth({"name": "x", "longitude": 181.0, "latitude": 0, "timezone": 8.0})},
    )
    assert bad_lon.status_code == 422, bad_lon.text


def test_place_timezone_defaults_to_utc8() -> None:
    resp = client.post(
        "/api/v1/charts/bazi",
        json={"birth": _birth({"name": "未填时区", "longitude": 116.4074, "latitude": 39.9042})},
    )
    assert resp.status_code == 200, resp.text
    warnings = " ".join(resp.json().get("warnings") or [])
    assert "UTC+8" in warnings
