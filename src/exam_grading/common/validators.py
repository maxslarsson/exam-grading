"""Validation utilities for exam grading package."""
from pathlib import Path


def validate_directory(path: Path, name: str = "Directory") -> None:
    """
    Validate that a path is a directory.
    
    Args:
        path: Path to validate
        name: Descriptive name for error messages
        
    Raises:
        ValueError: If path is not a directory
    """
    if not path.is_dir():
        raise ValueError(f"Error: {name} is not a valid directory: {path}")


def validate_file(path: Path, name: str = "File") -> None:
    """
    Validate that a path is a file.
    
    Args:
        path: Path to validate
        name: Descriptive name for error messages
        
    Raises:
        ValueError: If path is not a file
    """
    if not path.is_file():
        raise ValueError(f"Error: {name} not found: {path}")


def validate_csv_file(path: Path, name: str = "CSV file") -> None:
    """
    Validate that a path is a CSV file.
    
    Args:
        path: Path to validate
        name: Descriptive name for error messages
        
    Raises:
        ValueError: If path is not a valid CSV file
    """
    if not path.is_file() or path.suffix != ".csv":
        raise ValueError(f"Error: {name} is not a valid CSV: {path}")