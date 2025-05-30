"""Validation utilities for exam grading package.

This module provides reusable validation functions for file system paths,
ensuring consistent error handling across the application.
"""
from pathlib import Path


def validate_directory(path: Path, name: str = "Directory") -> None:
    """Validate that a path exists and is a directory.
    
    This function checks if the given path points to an existing directory.
    Used throughout the application to validate input and output directories
    before processing.
    
    Args:
        path: Path object to validate
        name: Descriptive name for the path, used in error messages
              (e.g., "Scan directory", "Output folder")
        
    Raises:
        ValueError: If path does not exist or is not a directory
        
    Example:
        >>> from pathlib import Path
        >>> validate_directory(Path("./scans"), "Scan directory")
        # Raises ValueError if ./scans doesn't exist or isn't a directory
    """
    if not path.is_dir():
        raise ValueError(f"Error: {name} is not a valid directory: {path}")


def validate_file(path: Path, name: str = "File") -> None:
    """Validate that a path exists and is a file.
    
    This function checks if the given path points to an existing file.
    Used to validate configuration files, CSVs, and other required files
    before attempting to read them.
    
    Args:
        path: Path object to validate
        name: Descriptive name for the file, used in error messages
              (e.g., "Configuration file", "Student roster")
        
    Raises:
        ValueError: If path does not exist or is not a file
        
    Example:
        >>> from pathlib import Path
        >>> validate_file(Path("./config.json"), "Configuration file")
        # Raises ValueError if config.json doesn't exist
    """
    if not path.is_file():
        raise ValueError(f"Error: {name} not found: {path}")


def validate_csv_file(path: Path, name: str = "CSV file") -> None:
    """Validate that a path exists, is a file, and has .csv extension.
    
    This function performs additional validation beyond validate_file()
    by checking that the file has a .csv extension. Used for validating
    data files like student rosters, bubble definitions, and grading results.
    
    Args:
        path: Path object to validate
        name: Descriptive name for the CSV file, used in error messages
              (e.g., "Student roster CSV", "Bubble positions file")
        
    Raises:
        ValueError: If path does not exist, is not a file, or doesn't
                   have a .csv extension
        
    Example:
        >>> from pathlib import Path
        >>> validate_csv_file(Path("./students.csv"), "Student roster")
        # Raises ValueError if students.csv doesn't exist or isn't a CSV
    """
    if not path.is_file() or path.suffix != ".csv":
        raise ValueError(f"Error: {name} is not a valid CSV: {path}")