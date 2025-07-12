"""
Custom exception classes for QRare.

Provides a hierarchy of specific exceptions for different error conditions,
enabling better error handling and user feedback throughout the application.
"""

from typing import Optional, List, Any


class QRareError(Exception):
    """
    Base exception class for all QRare-related errors.
    
    Provides common functionality for error reporting and context management.
    All other QRare exceptions inherit from this base class.
    """
    
    def __init__(self, message: str, details: Optional[str] = None, context: Optional[dict] = None):
        """
        Initialize QRare exception.
        
        Args:
            message: Primary error message describing what went wrong
            details: Optional additional details about the error
            context: Optional dictionary with relevant context information
        """
        self.message = message
        self.details = details
        self.context = context or {}
        
        # Create full error message
        full_message = message
        if details:
            full_message += f" Details: {details}"
        
        super().__init__(full_message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the error context.
        
        Args:
            key: Context key to retrieve
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        return self.context.get(key, default)


class ValidationError(QRareError):
    """
    Exception raised when input validation fails.
    
    Used for invalid file paths, unsupported formats, out-of-range parameters,
    and other input validation failures.
    """
    
    def __init__(self, parameter: str, value: Any, expected: str, **kwargs):
        """
        Initialize validation error.
        
        Args:
            parameter: Name of the parameter that failed validation
            value: The invalid value that was provided
            expected: Description of what was expected
            **kwargs: Additional arguments passed to base class
        """
        message = f"Invalid {parameter}: '{value}', expected {expected}"
        context = kwargs.get('context', {})
        context.update({
            'parameter': parameter,
            'value': value,
            'expected': expected
        })
        kwargs['context'] = context
        
        super().__init__(message, **kwargs)


class EncodingError(QRareError):
    """
    Exception raised during file-to-QR encoding process.
    
    Covers errors in file reading, compression, chunk processing,
    QR code generation, and image saving.
    """
    
    def __init__(self, operation: str, file_path: Optional[str] = None, **kwargs):
        """
        Initialize encoding error.
        
        Args:
            operation: Description of the operation that failed
            file_path: Optional path to the file being processed
            **kwargs: Additional arguments passed to base class
        """
        message = f"Encoding failed during {operation}"
        if file_path:
            message += f" for file: {file_path}"
        
        context = kwargs.get('context', {})
        context.update({
            'operation': operation,
            'file_path': file_path
        })
        kwargs['context'] = context
        
        super().__init__(message, **kwargs)


class DecodingError(QRareError):
    """
    Exception raised during QR-to-file decoding process.
    
    Covers errors in QR code reading, chunk validation, data decompression,
    file reconstruction, and integrity verification.
    """
    
    def __init__(self, operation: str, image_path: Optional[str] = None, **kwargs):
        """
        Initialize decoding error.
        
        Args:
            operation: Description of the operation that failed
            image_path: Optional path to the QR image being processed
            **kwargs: Additional arguments passed to base class
        """
        message = f"Decoding failed during {operation}"
        if image_path:
            message += f" for image: {image_path}"
        
        context = kwargs.get('context', {})
        context.update({
            'operation': operation,
            'image_path': image_path
        })
        kwargs['context'] = context
        
        super().__init__(message, **kwargs)


class CompressionError(QRareError):
    """
    Exception raised during data compression or decompression.
    
    Specific to zlib compression/decompression failures, including
    corrupted data, insufficient memory, or invalid compression parameters.
    """
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None, **kwargs):
        """
        Initialize compression error.
        
        Args:
            operation: Whether "compression" or "decompression" failed
            original_error: The underlying exception that caused this error
            **kwargs: Additional arguments passed to base class
        """
        message = f"Data {operation} failed"
        details = None
        
        if original_error:
            details = f"Underlying error: {str(original_error)}"
        
        context = kwargs.get('context', {})
        context.update({
            'operation': operation,
            'original_error': str(original_error) if original_error else None
        })
        kwargs['context'] = context
        
        super().__init__(message, details=details, **kwargs)


class IntegrityError(QRareError):
    """
    Exception raised when file integrity verification fails.
    
    Occurs when the reconstructed file's hash doesn't match the original hash,
    indicating data corruption during the encoding/decoding process.
    """
    
    def __init__(self, expected_hash: str, actual_hash: str, file_path: Optional[str] = None, **kwargs):
        """
        Initialize integrity error.
        
        Args:
            expected_hash: The expected file hash
            actual_hash: The actual computed hash
            file_path: Optional path to the file being verified
            **kwargs: Additional arguments passed to base class
        """
        message = "File integrity verification failed"
        details = f"Expected hash: {expected_hash}, actual hash: {actual_hash}"
        
        if file_path:
            message += f" for file: {file_path}"
        
        context = kwargs.get('context', {})
        context.update({
            'expected_hash': expected_hash,
            'actual_hash': actual_hash,
            'file_path': file_path
        })
        kwargs['context'] = context
        
        super().__init__(message, details=details, **kwargs)


class ChunkError(QRareError):
    """
    Exception raised when there are issues with chunk processing.
    
    Includes missing chunks, duplicate chunks, inconsistent metadata,
    or chunks that are out of sequence.
    """
    
    def __init__(self, issue: str, chunk_info: Optional[dict] = None, **kwargs):
        """
        Initialize chunk error.
        
        Args:
            issue: Description of the chunk-related issue
            chunk_info: Optional dictionary with chunk metadata
            **kwargs: Additional arguments passed to base class
        """
        message = f"Chunk processing error: {issue}"
        
        context = kwargs.get('context', {})
        if chunk_info:
            context.update(chunk_info)
        kwargs['context'] = context
        
        super().__init__(message, **kwargs)


class QRCodeError(QRareError):
    """
    Exception raised when QR code operations fail.
    
    Covers QR code generation failures, reading failures, and cases where
    QR codes cannot be decoded due to damage or incompatible formats.
    """
    
    def __init__(self, operation: str, qr_info: Optional[dict] = None, **kwargs):
        """
        Initialize QR code error.
        
        Args:
            operation: Description of the QR operation that failed
            qr_info: Optional dictionary with QR code information
            **kwargs: Additional arguments passed to base class
        """
        message = f"QR code {operation} failed"
        
        context = kwargs.get('context', {})
        if qr_info:
            context.update(qr_info)
        kwargs['context'] = context
        
        super().__init__(message, **kwargs)


class FileOperationError(QRareError):
    """
    Exception raised during file system operations.
    
    Covers file reading, writing, directory creation, and other
    file system related failures.
    """
    
    def __init__(self, operation: str, path: str, original_error: Optional[Exception] = None, **kwargs):
        """
        Initialize file operation error.
        
        Args:
            operation: Description of the file operation that failed
            path: File or directory path involved in the operation
            original_error: The underlying exception that caused this error
            **kwargs: Additional arguments passed to base class
        """
        message = f"File {operation} failed for path: {path}"
        details = None
        
        if original_error:
            details = f"System error: {str(original_error)}"
        
        context = kwargs.get('context', {})
        context.update({
            'operation': operation,
            'path': path,
            'original_error': str(original_error) if original_error else None
        })
        kwargs['context'] = context
        
        super().__init__(message, details=details, **kwargs)