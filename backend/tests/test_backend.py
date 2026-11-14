"""Offline tests: no network. Remote files are replaced by FITS files built in memory."""

import io

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from app import align, archive, pipeline, prepare, render

RA, DEC = 150.0, 20.0


def make_wcs(angle_deg=0.0, n=200):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [RA, DEC]
    w.wcs.crpix = [n / 2 + 0.5, n / 2 + 0.5]
    s, a = 6.14 / 3600, np.radians(angle_deg)
    w.wcs.cd = [[-s * np.cos(a), s * np.sin(a)], [s * np.sin(a), s * np.cos(a)]]
    return w


def make_file(compressed_flags: bool, n=200):
    rng = np.random.default_rng(1)
    image = rng.normal(5, 1, (n, n)).astype("f4")
    flags = rng.integers(0, 2**28, (n, n)).astype("i4")
    hdr = make_wcs(n=n).to_header()
    hdr["MJD-AVG"], hdr["DATE-AVG"] = 60900.5, "2025-08-13T12:00:00"
    flag_hdu = (fits.CompImageHDU(flags, name="FLAGS", compression_type="RICE_1", tile_shape=(1, n))
                if compressed_flags else fits.ImageHDU(flags, name="FLAGS"))
    hdus = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(image, hdr, name="IMAGE"), flag_hdu,
                         fits.ImageHDU(image * 2, name="VARIANCE")])
    buf = io.BytesIO()
    hdus.writeto(buf)
    return buf.getvalue(), image, flags


@pytest.fixture
def remote(monkeypatch):
    files = {}

    def read_range(url, start, length, tries=1):
        data = files[url]
        return data[start : start + length] if start >= 0 else data[-length:]

    monkeypatch.setattr(archive, "read_range", read_range)
    return files


@pytest.mark.parametrize("compressed", [False, True])
def test_cutout_matches_full_file(remote, compressed):
    remote["f"], image, flags = make_file(compressed)
    cut = archive.cutout("f", RA, DEC, 10, wanted=("IMAGE", "FLAGS", "VARIANCE"))
    x0, x1, y0, y1 = cut["box"]
    assert (x1 - x0, y1 - y0) == (21, 21)
    assert np.array_equal(cut["IMAGE"], image[y0:y1, x0:x1])
    assert np.array_equal(cut["FLAGS"], flags[y0:y1, x0:x1])
    assert np.array_equal(cut["VARIANCE"], image[y0:y1, x0:x1] * 2)


def test_cutout_is_clipped_at_the_detector_edge(remote):
    remote["f"], image, _ = make_file(False)
    ra, dec = make_wcs().pixel_to_world_values(2, 100)
    cut = archive.cutout("f", float(ra), float(dec), 10)
    assert cut["box"] == (0, 13, 90, 111)
    assert cut["IMAGE"].shape == (21, 13)


def test_cutout_cache_downloads_once(remote, tmp_path, monkeypatch):
    monkeypatch.setattr(archive.config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(archive, "wave_table", lambda url, det: None)
    remote["f"], _, _ = make_file(True)
    exposure = {"id": "x", "url": "f", "detector": 2, "mjd": 60900.0}
    first = archive.fetch_cutout(exposure, RA, DEC, 10)
    remote.clear()  # a second download would now fail
    second = archive.fetch_cutout(exposure, RA, DEC, 10)
    assert (first["cached"], second["cached"]) == (False, True)
    assert np.array_equal(first["image"], second["image"])
    assert second["mjd"] == 60900.5


def test_wavelength_interpolation():
    xs, ys = np.array([1.0, 1001.0, 2001.0]), np.array([1.0, 2001.0])
    values = np.zeros((2, 3, 2))
    values[..., 0] = [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]  # wavelength rises with y
    values[..., 1] = 0.03
    wave, width = archive.wavelength_at((xs, ys, values), 500, 1000)
    assert wave == pytest.approx(1.5, abs=1e-6) and width == pytest.approx(0.03)
    assert archive.wavelength_at(None, 0, 0) == (None, None)


def test_exposure_id_ignores_processing_version():
    url = "https://x/dr1/level2/2025W33_2C/l2b-v27-2026-228/3/level2_2025W33_2C_0321_1D3_spx_l2b-v27-2026-228.fits"
    assert archive.exposure_id(url) == "level2_2025W33_2C_0321_1D3"


def test_prepare_removes_background_and_repairs_pixels():
    rng = np.random.default_rng(2)
    image = rng.normal(10, 0.1, (41, 41)).astype("f4")
    flags = np.full(image.shape, 1 << prepare.FLAG_BITS["SOURCE"], "i4")  # "known source" everywhere
    image[18:23, 18:23] += 50  # a bright star...
    image[20, 20] = np.nan     # ...with a blown-out centre
    flags[20, 20] |= 1 << prepare.FLAG_BITS["OVERFLOW"]
    image[5, 5] = 500          # a cosmic-ray hit
    flags[5, 5] |= 1 << prepare.FLAG_BITS["TRANSIENT"]
    clean, stats = prepare.prepare(image, flags)
    assert np.isfinite(clean).all()
    assert abs(np.median(clean)) < 0.05 and stats["background"] == pytest.approx(10, abs=0.05)
    assert clean[20, 20] > 45        # the core is bright, not a black hole
    assert abs(clean[5, 5]) < 1      # the hit is gone
    assert stats["bad_fraction"] < 0.01  # the SOURCE flag is not counted as bad


def test_flag_names():
    assert prepare.flag_names((1 << 21) | 1) == ["TRANSIENT", "SOURCE"]


@pytest.mark.parametrize("angle", [0, 37, 180, 250])
def test_star_lands_on_the_same_pixel_at_any_rotation(angle):
    wcs = make_wcs(angle)
    ra, dec = RA + 0.01, DEC - 0.008
    x, y = wcs.world_to_pixel_values(ra, dec)
    yy, xx = np.mgrid[:200, :200]
    image = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / 2).astype("f4")
    grid, size, scale = align.target_grid(RA, DEC, 10.0)
    out = align.align(image, wcs, grid, size)
    assert out.shape == (size, size) and scale == pytest.approx(6.14 / 3)
    ey, ex = grid.world_to_pixel_values(ra, dec)[::-1]
    gy, gx = np.mgrid[:size, :size]
    weight = np.nan_to_num(out)
    cx, cy = (weight * gx).sum() / weight.sum(), (weight * gy).sum() / weight.sum()
    assert np.hypot(cx - ex, cy - ey) * scale < 0.5 * 6.14 / 3  # well under half a native pixel


def test_grid_is_north_up_east_left():
    grid, size, _ = align.target_grid(RA, DEC, 10.0)
    x_n, y_n = grid.world_to_pixel_values(RA, DEC + 0.01)
    x_e, y_e = grid.world_to_pixel_values(RA + 0.01, DEC)
    centre = (size - 1) / 2
    assert y_n > centre and x_n == pytest.approx(centre, abs=0.01)
    assert x_e < centre
    assert align.cutout_half_size(10.0) * 2 * 6.14 > 600 * np.sqrt(2)


def test_png_is_flipped_and_handles_blank_pixels():
    from PIL import Image

    frame = np.zeros((4, 4), "f4")
    frame[3, 0] = 100   # top-left on the sky (last FITS row)
    frame[0, 3] = np.nan
    low, high, soft = render.stretch_limits([frame], 1.0)
    pixels = np.array(Image.open(io.BytesIO(render.to_png(frame, low, high, soft))))
    assert pixels.shape == (4, 4) and pixels[0, 0] == 255 and pixels[3, 3] == 0


def test_seasons_and_even_pick():
    assert pipeline.assign_seasons([1, 2, 31, 70, 71, 200]) == [0, 0, 0, 1, 1, 2]
    picked = pipeline.pick_evenly(list(range(100)), 10)
    assert len(picked) == 10 and picked[0] == 0 and picked[-1] == 99
    assert pipeline.pick_evenly([1, 2], 10) == [1, 2]


def test_api_rejects_bad_input_and_serves_cached_result(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app import config, main

    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    client = TestClient(main.app)
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/frames", params={"ra": 400, "dec": 0}).status_code == 422
    assert client.get("/api/frames", params={"ra": 10, "dec": 0, "fov": 500}).status_code == 422
    assert client.get("/api/frames", params={"ra": 10, "dec": 0, "band": 7}).status_code == 422
    assert client.get("/api/frame/../../etc/passwd.png").status_code == 404
    assert client.get("/api/frame/0123456789abcdef/000.png").status_code == 404

    key = pipeline.request_key(10.0, 0.0, 10.0, 2, "exposures")
    path = pipeline.result_path(key)
    path.parent.mkdir(parents=True)
    path.write_text('{"status": "done", "frames": []}')
    (path.parent / "000.png").write_bytes(b"png")
    assert client.get("/api/frames", params={"ra": 10, "dec": 0}).json() == {"status": "done", "frames": []}
    assert client.get(f"/api/frame/{key}/000.png").content == b"png"
