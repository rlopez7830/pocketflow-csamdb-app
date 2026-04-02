"""ARIES VID and image path lookup utilities.

Queries A_Ube_Unit_Hist2 for VID history and A_OBJ_* tables for image paths.
"""

import logging

from utils.pyuber_client import execute_query, ARIES_DATASOURCE

logger = logging.getLogger(__name__)

OPERATIONS = ("3040", "3041")


def _build_in_clause(prefix, values):
    """Build a parameterised IN clause and its parameter dict."""
    params = {f"{prefix}_{i}": v for i, v in enumerate(values)}
    placeholders = ", ".join(f":{k}" for k in params)
    return placeholders, params


def query_aries_vid(vid):
    """Query ARIES for the VID under operations 3040 and 3041.

    Args:
        vid: The Visual ID to look up.

    Returns:
        A list of dicts with keys: visual_id, lot_1, operation_1.
    """
    sql = (
        "SELECT "
        "u0.visualid AS visual_id, "
        "u0.lotnum AS lot_1, "
        "u0.ws_operation AS operation_1 "
        "FROM A_Ube_Unit_Hist2 u0 "
        "WHERE u0.ws_operation IN (:op1, :op2) "
        "AND u0.visualid = :vid"
    )

    params = {"vid": vid, "op1": OPERATIONS[0], "op2": OPERATIONS[1]}

    logger.info("Querying ARIES for VID=%s at operations %s", vid, OPERATIONS)
    return execute_query(sql, ARIES_DATASOURCE, params=params)


def query_aries_image_paths(aries_results):
    """Query ARIES A_OBJ_* tables for CSAM image file paths.

    Uses lots and VIDs from the initial ARIES query results to find
    image file paths through the FCM module session data.

    Args:
        aries_results: A list of dicts from query_aries_vid, each containing
            lot_1, operation_1, and visual_id keys.

    Returns:
        A list of dicts with keys: lot, operation, visual_id,
        image_filer_address, image_relative_path, parameter_value.
    """
    lots = list({str(r["lot_1"]) for r in aries_results})
    vids = list({str(r["visual_id"]) for r in aries_results})
    lot_ph, lot_params = _build_in_clause("lot", lots)
    vid_ph, vid_params = _build_in_clause("vid", vids)

    sql = (
        "SELECT DISTINCT "
        "a0.lot AS lot, "
        "a0.operation AS operation, "
        "a6.visual_id AS visual_id, "
        "a0.image_filer_address AS image_filer_address, "
        "a0.image_relative_path AS image_relative_path, "
        "COALESCE(a9.string_val_3, a9.string_val_1) AS parameter_value "
        "FROM A_OBJ_SESSION a0 "
        "LEFT JOIN A_OBJ_MEDIA_TESTING a3 "
        "ON a3.lao_start_ww = a0.lao_start_ww AND a3.obj_s_id = a0.obj_s_id "
        "LEFT JOIN A_OBJ_UNIT_TESTING a6 "
        "ON a6.lao_start_ww = a3.lao_start_ww AND a6.obj_s_id = a3.obj_s_id "
        "AND a6.obj_mt_id = a3.obj_mt_id "
        "LEFT JOIN A_OBJ_UNIT_DATA a9 "
        "ON a9.lao_start_ww = a6.lao_start_ww AND a9.obj_s_id = a6.obj_s_id "
        "AND a9.obj_mt_id = a6.obj_mt_id AND a9.obj_ut_id = a6.obj_ut_id "
        "AND a9.data_source = 'DEVICEDATA' "
        "WHERE a0.module_name IN ('FCM') "
        f"AND a6.visual_id IN ({vid_ph}) "
        "AND a0.operation IN (:op1, :op2) "
        f"AND a0.lot IN ({lot_ph}) "
        "AND a9.parameter_name = 'IMAGE_NAME'"
    )

    params = {
        **lot_params,
        **vid_params,
        "op1": OPERATIONS[0],
        "op2": OPERATIONS[1],
    }

    logger.info("Querying ARIES image paths for lots=%s, vids=%s", lots, vids)
    return execute_query(sql, ARIES_DATASOURCE, params=params)
