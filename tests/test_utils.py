import math

import pytest

from nodc_station import utils


@pytest.mark.parametrize(
    "given_sweref_99_tm_latitude, given_sweref_99_tm_longitude, "
    "expected_wgs84_latitude, expected_wgs84_longitude",
    (
            ("6493985", "566748", 58.581150, 16.147924),
            ("6397919", "314353", 57.685112, 11.885881),
    )
)
def test_transform_ref_system(
        given_sweref_99_tm_latitude,
        given_sweref_99_tm_longitude,
        expected_wgs84_latitude,
        expected_wgs84_longitude
):
    wgs84_latitude, wgs84_longitude = utils.transform_ref_system(
        latitude=given_sweref_99_tm_latitude, longitude=given_sweref_99_tm_longitude
    )

    assert math.isclose(float(wgs84_latitude), expected_wgs84_latitude, abs_tol=10e-6)
    assert math.isclose(float(wgs84_longitude), expected_wgs84_longitude, abs_tol=10e-6)
