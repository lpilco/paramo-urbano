"""Geographic privacy obfuscation middleware enforcing a 500-meter privacy radius."""

import json
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

PRIVACY_RADIUS_METERS = 500.0
EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in meters using Haversine formula."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def _extract_lat_lon(point: Union[Dict[str, Any], List[Any], Tuple[Any, ...]]) -> Optional[Tuple[float, float]]:
    """Extract (lat, lon) from various telemetry representations."""
    if isinstance(point, dict):
        lat = None
        for key in ("latitude", "lat"):
            if key in point and point[key] is not None:
                lat = point[key]
                break

        lon = None
        for key in ("longitude", "lon", "lng"):
            if key in point and point[key] is not None:
                lon = point[key]
                break

        if lat is not None and lon is not None:
            try:
                return float(lat), float(lon)
            except (ValueError, TypeError):
                return None
    elif isinstance(point, (list, tuple)) and len(point) >= 2:
        try:
            return float(point[0]), float(point[1])
        except (ValueError, TypeError):
            return None
    return None


def obfuscate_gps_points(
    points: List[Any],
    radius_meters: float = PRIVACY_RADIUS_METERS,
) -> List[Any]:
    """Truncate or filter out telemetry points located within 500 meters of origin and destination.

    Args:
        points (List[Any]): Sequential list of GPS coordinates or coordinate objects.
        radius_meters (float, optional): Privacy buffer radius in meters. Defaults to 500.0.

    Returns:
        List[Any]: Sanitized sequence of points with origin/arrival privacy zones removed.
    """
    if len(points) < 3:
        return points

    origin_coords = _extract_lat_lon(points[0])
    destination_coords = _extract_lat_lon(points[-1])

    if origin_coords is None or destination_coords is None:
        return points

    origin_lat, origin_lon = origin_coords
    dest_lat, dest_lon = destination_coords

    sanitized_points: List[Any] = []
    for pt in points:
        coords = _extract_lat_lon(pt)
        if coords is None:
            continue

        lat, lon = coords
        dist_from_origin = haversine_distance_meters(lat, lon, origin_lat, origin_lon)
        dist_from_dest = haversine_distance_meters(lat, lon, dest_lat, dest_lon)

        # Truncate / omit points within the 500m privacy circle of start or finish
        if dist_from_origin > radius_meters and dist_from_dest > radius_meters:
            sanitized_points.append(pt)

    return sanitized_points


def _process_json_privacy(data: Any) -> Any:
    """Recursively traverse JSON-like data and obfuscate recognized coordinate collections."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key in ("telemetry_points", "coordinates", "track_points", "points") and isinstance(value, list):
                sanitized[key] = obfuscate_gps_points(value)
            else:
                sanitized[key] = _process_json_privacy(value)
        return sanitized
    elif isinstance(data, list):
        return [_process_json_privacy(item) for item in data]
    return data


class GeographicPrivacyMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing 500-meter privacy radius on outgoing telemetry payloads."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Intercept responses containing GPS time-series and apply geographic privacy filter."""
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type and "application/problem+json" not in content_type:
            return response

        # Read streaming body
        body_chunks = [chunk async for chunk in response.body_iterator]
        body_bytes = b"".join(body_chunks)

        if not body_bytes:
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        try:
            parsed = json.loads(body_bytes.decode("utf-8"))
            filtered = _process_json_privacy(parsed)
            new_bytes = json.dumps(filtered).encode("utf-8")

            # Clone headers and update Content-Length
            headers = dict(response.headers)
            headers["content-length"] = str(len(new_bytes))

            return Response(
                content=new_bytes,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )
        except Exception:
            # If payload is unparseable or error occurs, return original body safely
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
