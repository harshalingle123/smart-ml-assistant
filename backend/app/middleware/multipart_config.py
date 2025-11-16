"""
Middleware to configure multipart form parser for large file uploads
"""
from starlette.requests import Request
from starlette.datastructures import FormData, UploadFile
from starlette.formparsers import MultiPartParser
from typing import Tuple
from app.core.config import settings


class LargeFileMultiPartParser(MultiPartParser):
    """
    Custom MultiPartParser that allows large file uploads
    """
    max_file_size = settings.MAX_UPLOAD_SIZE

    def __init__(self, headers, stream):
        super().__init__(
            headers,
            stream,
            max_files=1000,
            max_fields=1000
        )
        # Override max_file_size for this instance
        self.max_file_size = settings.MAX_UPLOAD_SIZE


# Monkey patch Request.form() to use our custom parser
original_parse_body = Request._parse_body


async def custom_parse_body(self) -> Tuple[FormData, UploadFile]:
    """
    Custom form parser that uses increased limits
    """
    if not hasattr(self, "_form"):
        content_type_header = self.headers.get("Content-Type")
        content_type, _ = self._parse_content_header(content_type_header)

        if content_type == b"multipart/form-data":
            # Use our custom parser with larger limits
            from starlette.formparsers import FormParser
            from multipart.multipart import QuerystringParser
            import typing

            # Patch the multipart module to accept larger fields
            import multipart.multipart as mp

            # Increase the max size for field parsing
            if hasattr(mp, 'Field'):
                original_field_init = mp.Field.__init__

                def patched_field_init(field_self, name, **kwargs):
                    # Set a much larger buffer size
                    kwargs['max_size'] = settings.MAX_UPLOAD_SIZE
                    return original_field_init(field_self, name, **kwargs)

                mp.Field.__init__ = patched_field_init

            # Now call original parse
            return await original_parse_body(self)
        else:
            return await original_parse_body(self)

    return self._form


Request._parse_body = custom_parse_body
