"""MARS candidate directory lookup utility.

Queries MARS for CSAM directory metadata using lot and operation values
returned by the ARIES lookup.
"""

import logging

from utils.pyuber_client import execute_query, MARS_DATASOURCE

logger = logging.getLogger(__name__)


def _build_in_clause(prefix, values):
    """Build a parameterised IN clause and its parameter dict.

    Returns:
        (placeholder_sql, params_dict)  e.g. (":p0, :p1", {"p0": "A", "p1": "B"})
    """
    params = {f"{prefix}_{i}": v for i, v in enumerate(values)}
    placeholders = ", ".join(f":{k}" for k in params)
    return placeholders, params


def query_mars_candidates(aries_results):
    """Query MARS for CSAM directory candidates.

    Args:
        aries_results: A list of dicts from the ARIES lookup, each containing
            lot_1 and operation_1 keys.

    Returns:
        A list of dicts with keys including pkg_epoxy_lot, operation,
        work_week_thru_epoxy_csam, ww, pkg_epoxy_entity, and pkg_csam_dir.
    """
    lots = list({str(r["lot_1"]) for r in aries_results})
    operations = list({str(r["operation_1"]) for r in aries_results})

    lot_placeholders, lot_params = _build_in_clause("lot", lots)
    op_placeholders, op_params = _build_in_clause("op", operations)

    sql = (
        "SELECT "
        "sub.pkg_epoxy_lot, "
        "sub.operation, "
        "sub.work_week_thru_epoxy_csam, "
        "sub.WW, "
        "sub.pkg_epoxy_entity, "
        r"'\\atdfile1\dfM_IMAGE\' || 'WW' || sub.WW || '_' "
        "|| SUBSTR(sub.work_week_thru_epoxy_csam, 1, 4) "
        r"|| '\' || sub.operation || '\' || sub.pkg_epoxy_entity "
        r"|| '\' || sub.pkg_epoxy_lot || '\' AS PKG_CSAM_DIR "
        "FROM ( "
        "SELECT "
        "v2.lot AS pkg_epoxy_lot, "
        "v0.operation AS operation, "
        "c0.ww AS work_week_thru_epoxy_csam, "
        "CASE WHEN SUBSTR(c0.ww, -2, 1) = '0' "
        "THEN SUBSTR(c0.ww, -1) "
        "ELSE SUBSTR(c0.ww, -2) END AS WW, "
        "v0.entity AS pkg_epoxy_entity "
        "FROM "
        "A43_PROD_0.F_Lot v2, "
        "A43_PROD_0.F_EntityLotHist v0, "
        "A43_PROD_0.F_Calendar c0 "
        "WHERE "
        "v2.lot = v0.lot "
        "AND v0.history_deleted_flag = 'N' "
        "AND v0.txn_date BETWEEN c0.start_date (+) AND c0.end_date (+) "
        "AND c0.event_code (+) = 'S' "
        "AND c0.facility (+) = v0.facility "
        f"AND v2.lot IN ({lot_placeholders}) "
        f"AND v0.operation IN ({op_placeholders}) "
        ") sub"
    )

    params = {**lot_params, **op_params}

    logger.info(
        "Querying MARS for lots=%s, operations=%s", lots, operations
    )
    return execute_query(sql, MARS_DATASOURCE, params=params)
