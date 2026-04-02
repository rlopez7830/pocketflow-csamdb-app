import logging

from pocketflow import Node

from utils.db_aries import query_aries_vid, query_aries_image_paths
from utils.path_builder import build_image_paths
from utils.image_identity import assign_image_ids, resolve_image_by_id
from utils.image_loader import load_tiff
from utils.image_convert import convert_tiff_first_page_to_png
from utils.image_resize import resize_image
from utils.responses import build_lookup_success, build_lookup_error

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lookup Flow Nodes
# ---------------------------------------------------------------------------

class ValidateInputNode(Node):
    """Ensure the request contains a non-empty VID."""

    def prep(self, shared):
        return shared["request"].get("vid", "")

    def exec(self, vid):
        return bool(vid and vid.strip())

    def post(self, shared, prep_res, exec_res):
        if not exec_res:
            shared["response"]["error"] = "VID input is required."
            return "error"
        shared["validation"]["input_present"] = True


class QueryAriesHistoryNode(Node):
    """Query ARIES for the VID under operations 3040/3041."""

    def prep(self, shared):
        return shared["request"]["vid"]

    def exec(self, vid):
        return query_aries_vid(vid)

    def post(self, shared, prep_res, exec_res):
        shared["manufacturing"]["aries_results"] = exec_res


class CheckAriesResultNode(Node):
    """Stop the flow if ARIES returned no results."""

    def prep(self, shared):
        return shared["manufacturing"]["aries_results"]

    def exec(self, aries_results):
        return len(aries_results) > 0

    def post(self, shared, prep_res, exec_res):
        if not exec_res:
            shared["response"]["error"] = (
                "VID was not found. It either does not exist or was not run "
                "at operations 3040/3041. Please check again."
            )
            return "not_found"


class QueryAriesImagePathsNode(Node):
    """Query ARIES A_OBJ_* tables for image file paths."""

    def prep(self, shared):
        return shared["manufacturing"]["aries_results"]

    def exec(self, aries_results):
        return query_aries_image_paths(aries_results)

    def post(self, shared, prep_res, exec_res):
        shared["manufacturing"]["image_path_results"] = exec_res
        logger.info("ARIES image path query returned %d row(s)", len(exec_res))
        if not exec_res:
            shared["response"]["error"] = (
                "No CSAM image path data found in the manufacturing system."
            )
            return "no_paths"


class BuildImagePathsNode(Node):
    """Construct and validate UNC image paths from query results."""

    def prep(self, shared):
        return shared["manufacturing"]["image_path_results"]

    def exec(self, image_path_results):
        return build_image_paths(image_path_results)

    def post(self, shared, prep_res, exec_res):
        shared["filesystem"]["matched_images"] = exec_res
        if not exec_res:
            shared["response"]["error"] = (
                "No valid CSAM image files were found at the resolved paths."
            )
            return "no_images"


class AssignImageIDsNode(Node):
    """Generate image IDs and store them in the in-memory cache."""

    def prep(self, shared):
        return shared["filesystem"]["matched_images"]

    def exec(self, matched_images):
        return assign_image_ids(matched_images)

    def post(self, shared, prep_res, exec_res):
        shared["filesystem"]["matched_images"] = exec_res


class BuildLookupResponseNode(Node):
    """Build the final lookup response payload."""

    def prep(self, shared):
        return shared

    def exec(self, shared):
        if shared["response"].get("error"):
            return build_lookup_error(
                shared["request"]["vid"],
                shared["response"]["error"],
            )
        return build_lookup_success(shared)

    def post(self, shared, prep_res, exec_res):
        shared["response"]["lookup_result"] = exec_res


# ---------------------------------------------------------------------------
# Image Delivery Flow Nodes
# ---------------------------------------------------------------------------

class ResolveImageByIDNode(Node):
    """Resolve a cached image record by image_id."""

    def prep(self, shared):
        return shared["request"]["image_id"]

    def exec(self, image_id):
        return resolve_image_by_id(image_id)

    def post(self, shared, prep_res, exec_res):
        if exec_res is None:
            shared["response"]["error"] = (
                "Image reference not found or has expired. "
                "Please run the lookup again."
            )
            return "error"
        shared["filesystem"]["resolved_image"] = exec_res


class LoadTIFFNode(Node):
    """Load a TIFF file from the resolved path."""

    def prep(self, shared):
        return shared["filesystem"]["resolved_image"]["absolute_path"]

    def exec(self, file_path):
        return load_tiff(file_path)

    def post(self, shared, prep_res, exec_res):
        shared["image"]["binary_content"] = exec_res


class ConvertFirstPageToPNGNode(Node):
    """Convert the first TIFF page to PNG."""

    def prep(self, shared):
        return shared["image"]["binary_content"]

    def exec(self, tiff_bytes):
        return convert_tiff_first_page_to_png(tiff_bytes)

    def post(self, shared, prep_res, exec_res):
        shared["image"]["binary_content"] = exec_res


class ResizeImageNode(Node):
    """Resize the PNG to browser-friendly dimensions."""

    def prep(self, shared):
        return shared["image"]["binary_content"]

    def exec(self, png_bytes):
        return resize_image(png_bytes)

    def post(self, shared, prep_res, exec_res):
        resized_bytes, mime_type = exec_res
        shared["image"]["binary_content"] = resized_bytes
        shared["image"]["mime_type"] = mime_type


class BuildImageResponseNode(Node):
    """Package the final image response."""

    def prep(self, shared):
        return shared

    def exec(self, shared):
        return {
            "binary_content": shared["image"].get("binary_content"),
            "mime_type": shared["image"].get("mime_type", "image/png"),
            "error": shared["response"].get("error"),
        }

    def post(self, shared, prep_res, exec_res):
        shared["response"]["image_result"] = exec_res