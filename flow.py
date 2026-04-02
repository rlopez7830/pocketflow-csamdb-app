from pocketflow import Flow

from nodes import (
    ValidateInputNode,
    QueryAriesHistoryNode,
    CheckAriesResultNode,
    QueryAriesImagePathsNode,
    BuildImagePathsNode,
    AssignImageIDsNode,
    BuildLookupResponseNode,
    ResolveImageByIDNode,
    LoadTIFFNode,
    ConvertFirstPageToPNGNode,
    ResizeImageNode,
    BuildImageResponseNode,
)


def create_lookup_flow():
    """Build the VID lookup flow (7 nodes)."""
    validate_input = ValidateInputNode()
    query_aries = QueryAriesHistoryNode()
    check_aries = CheckAriesResultNode()
    query_image_paths = QueryAriesImagePathsNode()
    build_paths = BuildImagePathsNode()
    assign_ids = AssignImageIDsNode()
    build_response = BuildLookupResponseNode()

    # Happy path
    validate_input >> query_aries
    query_aries >> check_aries
    check_aries >> query_image_paths
    query_image_paths >> build_paths
    build_paths >> assign_ids
    assign_ids >> build_response

    # Error shortcuts
    validate_input - "error" >> build_response
    check_aries - "not_found" >> build_response
    query_image_paths - "no_paths" >> build_response
    build_paths - "no_images" >> build_response

    return Flow(start=validate_input)


def create_image_delivery_flow():
    """Build the image delivery flow (5 nodes)."""
    resolve_image = ResolveImageByIDNode()
    load_tiff = LoadTIFFNode()
    convert_png = ConvertFirstPageToPNGNode()
    resize = ResizeImageNode()
    build_response = BuildImageResponseNode()

    # Happy path
    resolve_image >> load_tiff
    load_tiff >> convert_png
    convert_png >> resize
    resize >> build_response

    # Error shortcut
    resolve_image - "error" >> build_response

    return Flow(start=resolve_image)