"""PyUber client utility for executing SQL queries against manufacturing databases."""

import logging
import os

import PyUber

logger = logging.getLogger(__name__)

# Datasource names – override via environment variables for your site.
ARIES_DATASOURCE = os.environ.get("PYUBER_ARIES_DATASOURCE", "ATD_PROD_ARIES")
MARS_DATASOURCE = os.environ.get("PYUBER_MARS_DATASOURCE", "ATD_PROD_MARS")


def execute_query(sql, datasource, params=None):
    """Execute a SQL query using PyUber and return results as a list of dicts.

    Args:
        sql: The SQL query string to execute.  Use ``:param_name`` for
            named bind variables.
        datasource: The PyUber datasource identifier (e.g. ``ATD_ARIES``).
        params: Optional dict of named parameters to bind into the query.

    Returns:
        A list of dicts (one per row) with **lower-cased** column-name keys.
    """
    logger.info("Executing query on datasource %s", datasource)
    logger.debug("SQL: %s | params: %s", sql, params)

    conn = PyUber.connect(datasource=datasource, row_factory=PyUber.DictionaryRow)
    cursor = conn.cursor()

    if params:
        cursor.execute(sql, parameters=params)
    else:
        cursor.execute(sql)

    rows = cursor.fetchall()

    # Oracle returns uppercase column names – normalise to lowercase so the
    # rest of the application can use a consistent naming convention.
    rows = [{k.lower(): v for k, v in row.items()} for row in rows]

    logger.info("Query returned %d row(s)", len(rows))
    return rows
