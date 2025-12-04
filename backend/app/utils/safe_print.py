"""
Safe printing utility for Windows console encoding issues
Handles Unicode characters that can't be displayed in Windows cp1252 encoding
"""
import sys


def safe_print(*args, **kwargs):
    """
    Print function that handles Unicode encoding errors on Windows
    Replaces problematic Unicode characters with ASCII equivalents
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Replace Unicode characters with ASCII equivalents
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common Unicode characters
                safe_str = arg.replace('✓', '[OK]')
                safe_str = safe_str.replace('✗', '[X]')
                safe_str = safe_str.replace('⚠', '[!]')
                safe_str = safe_str.replace('💬', '[MSG]')
                safe_str = safe_str.replace('🔍', '[SEARCH]')
                safe_str = safe_str.replace('❌', '[ERROR]')
                safe_str = safe_str.replace('⏳', '[WAIT]')
                safe_str = safe_str.replace('📦', '[PKG]')
                safe_str = safe_str.replace('🔍', '[FIND]')
                safe_args.append(safe_str)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


def configure_utf8_output():
    """
    Configure sys.stdout to use UTF-8 encoding
    Call this at application startup
    """
    if sys.platform == 'win32':
        try:
            # Try to set console to UTF-8 mode
            import io
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace'
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer,
                encoding='utf-8',
                errors='replace'
            )
        except Exception:
            # If that fails, we'll just use safe_print
            pass
