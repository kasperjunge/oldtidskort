from oldtidskort.core.geo import in_denmark, utm32_to_wgs84


def test_utm32_konvertering_lander_i_danmark():
    lon, lat = utm32_to_wgs84(575000, 6225000)  # ca. København
    assert in_denmark(lon, lat)
    assert round(lat) == 56


def test_punkt_uden_for_danmark_afvises():
    assert not in_denmark(2.35, 48.85)  # Paris
