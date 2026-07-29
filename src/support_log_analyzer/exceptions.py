"""Domain-specific exceptions presented as clear CLI errors."""


class LogAnalyzerError(Exception):
    """Base exception for expected application failures."""


class InputFileError(LogAnalyzerError):
    """Raised when an input log cannot be read or is empty."""


class UnsupportedFormatError(LogAnalyzerError):
    """Raised when a requested input or report format is unsupported."""


class ReportWriteError(LogAnalyzerError):
    """Raised when an exported report cannot be written."""
