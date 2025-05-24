import asyncio
import h3
import requests
from shapely.geometry import shape, Polygon, MultiPolygon, mapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.monitoring.models import HexGridCell
from geoalchemy2.shape import from_shape
from fastapi import APIRouter

router = APIRouter()    

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

@router.get("/populate-hex-grid")
async def populate_hex_grid():
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(select(HexGridCell))).scalars().all()
        if existing:
            print(f"Found {len(existing)} existing hex cells. Skipping population.")
            return

        # 1) Получаем GeoJSON из Nominatim
        params = {
            "city": "Astana",
            "country": "Kazakhstan",
            "format": "geojson",
            "polygon_geojson": 1,
        }
        resp = requests.get(NOMINATIM_URL, params=params,
                            headers={"User-Agent": "utm-app/1.0"})
        resp.raise_for_status()

        features = resp.json().get("features", [])
        if not features:
            raise RuntimeError("Не удалось получить границы Astana")

        geom = shape(features[0]["geometry"])
        # 2) Нормализуем в список Polygon
        if isinstance(geom, Polygon):
            polygons = [geom]
        elif isinstance(geom, MultiPolygon):
            polygons = list(geom.geoms)
        else:
            raise ValueError(f"Unsupported geometry type: {geom.geom_type}")

        # 3) Собираем все H3-индексы
        all_indexes = set()
        for poly in polygons:
            gj = mapping(poly)
            idxs = h3.polyfill(gj, res=8, geo_json_conformant=True)
            all_indexes.update(idxs)

        print(f"Generated {len(all_indexes)} H3 indexes")

        # 4) Вставка в БД батчами
        batch_size = 1000
        indexes_list = list(all_indexes)
        for i in range(0, len(indexes_list), batch_size):
            batch = indexes_list[i : i + batch_size]
            cells = []
            for idx in batch:
                lat, lng = h3.h3_to_geo(idx)
                boundary = h3.h3_to_geo_boundary(idx, geo_json=True)
                poly = Polygon(boundary)
                cells.append(
                    HexGridCell(
                        h3_index=idx,
                        center_lat=lat,
                        center_lng=lng,
                        geometry=from_shape(poly, srid=4326),
                    )
                )
            db.add_all(cells)
            await db.commit()
            print(f"Inserted {len(cells)} hex cells")

        print("Finished populating hex grid")
