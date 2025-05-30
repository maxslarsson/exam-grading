"""Helper functions for anonymizing and de-anonymizing student IDs.

This module provides functionality to maintain student privacy when interacting
with external services. It manages bidirectional mappings between real student
IDs and anonymous IDs, ensuring that sensitive data can be protected while
maintaining the ability to restore original identities when needed.
"""
import pandas as pd
from pathlib import Path
from typing import Dict


class StudentAnonymizer:
    """Handles mapping between student IDs and anonymous IDs.
    
    This class manages the anonymization and de-anonymization of student IDs
    for privacy protection when uploading data to external services. It loads
    mappings from a CSV file and provides methods to convert between real and
    anonymous IDs in both individual values and filenames.
    
    Attributes:
        students_csv_path: Path to the CSV file containing ID mappings
        student_to_anon: Dictionary mapping real IDs to anonymous IDs
        anon_to_student: Dictionary mapping anonymous IDs back to real IDs
    """
    
    def __init__(self, students_csv_path: str):
        """Initialize the anonymizer with student data.
        
        Args:
            students_csv_path: Path to students CSV file containing studentID 
                             and anonymousID columns
                             
        Raises:
            FileNotFoundError: If the students CSV file doesn't exist
            ValueError: If required columns are missing from the CSV
        """
        self.students_csv_path = Path(students_csv_path)
        self.student_to_anon: Dict[str, str] = {}
        self.anon_to_student: Dict[str, str] = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load student ID mappings from CSV file.
        
        This private method reads the students CSV and builds bidirectional
        dictionaries for fast lookup of anonymization mappings. All IDs are
        stored as strings to handle various ID formats consistently.
        
        Expected CSV format:
            studentID,anonymousID,first_name,last_name,email
            abc123,student_001,Alice,Smith,alice@example.edu
            def456,student_002,Bob,Jones,bob@example.edu
        """
        if not self.students_csv_path.exists():
            raise FileNotFoundError(f"Students CSV not found: {self.students_csv_path}")
        
        students_df = pd.read_csv(self.students_csv_path)
        
        # Check for required columns
        if 'studentID' not in students_df.columns:
            raise ValueError("Students CSV missing required column: studentID")
        
        # Check if anonymousID column exists
        if 'anonymousID' not in students_df.columns:
            raise ValueError("Students CSV missing required column: anonymousID. Cannot proceed without proper anonymization mappings.")
        
        # Build bidirectional mappings
        # Convert all IDs to strings to handle mixed types gracefully
        for _, row in students_df.iterrows():
            student_id = str(row['studentID'])
            anon_id = str(row['anonymousID'])
            self.student_to_anon[student_id] = anon_id
            self.anon_to_student[anon_id] = student_id
    
    def anonymize(self, student_id: str) -> str:
        """Convert student ID to anonymous ID.
        
        This method looks up the anonymous ID corresponding to a given student ID.
        The input is converted to string to handle various ID formats consistently.
        
        Args:
            student_id: The student's real ID (e.g., "abc123")
            
        Returns:
            The anonymous ID (e.g., "student_001")
            
        Raises:
            ValueError: If no mapping found for the student ID
            
        Example:
            >>> anonymizer = StudentAnonymizer("students.csv")
            >>> anonymizer.anonymize("abc123")
            'student_001'
        """
        student_id_str = str(student_id)
        if student_id_str not in self.student_to_anon:
            raise ValueError(f"No anonymization mapping found for student ID: {student_id}")
        return self.student_to_anon[student_id_str]
    
    def deanonymize(self, anon_id: str) -> str:
        """Convert anonymous ID back to student ID.
        
        This method reverses the anonymization process, looking up the real
        student ID corresponding to an anonymous ID.
        
        Args:
            anon_id: The anonymous ID (e.g., "student_001")
            
        Returns:
            The student's real ID (e.g., "abc123")
            
        Raises:
            ValueError: If no mapping found for the anonymous ID
            
        Example:
            >>> anonymizer = StudentAnonymizer("students.csv")
            >>> anonymizer.deanonymize("student_001")
            'abc123'
        """
        anon_id_str = str(anon_id)
        if anon_id_str not in self.anon_to_student:
            raise ValueError(f"No de-anonymization mapping found for anonymous ID: {anon_id}")
        return self.anon_to_student[anon_id_str]
    
    def anonymize_filename(self, filename: str) -> str:
        """Anonymize student IDs in a filename.
        
        This method searches for any student ID within a filename and replaces
        it with the corresponding anonymous ID. It's designed to work with
        filenames like "abc123_page1.pdf" → "student_001_page1.pdf".
        
        Args:
            filename: Original filename containing student ID
            
        Returns:
            Filename with student ID replaced by anonymous ID
            
        Raises:
            ValueError: If filename contains an unmapped student ID
            
        Example:
            >>> anonymizer = StudentAnonymizer("students.csv")
            >>> anonymizer.anonymize_filename("abc123_exam.pdf")
            'student_001_exam.pdf'
            
        Note:
            The method checks all known student IDs to find matches within
            the filename, not just at the beginning.
        """
        # Try to find and replace any known student ID in the filename
        for student_id, anon_id in self.student_to_anon.items():
            if student_id in filename:
                return filename.replace(student_id, anon_id)
        
        # If no match found, check if filename starts with an unknown ID
        # This helps catch cases where the student ID isn't in our mapping
        filename_parts = filename.split('_')
        if filename_parts and filename_parts[0] not in self.student_to_anon:
            raise ValueError(f"Filename '{filename}' appears to contain unmapped student ID: {filename_parts[0]}")
        return filename
    
    def deanonymize_filename(self, filename: str) -> str:
        """Restore student IDs in a filename.
        
        This method searches for any anonymous ID within a filename and replaces
        it with the corresponding real student ID. It reverses the anonymization
        done by anonymize_filename().
        
        Args:
            filename: Filename containing anonymous ID
            
        Returns:
            Filename with anonymous ID replaced by student ID
            
        Raises:
            ValueError: If filename contains an unmapped anonymous ID
            
        Example:
            >>> anonymizer = StudentAnonymizer("students.csv")
            >>> anonymizer.deanonymize_filename("student_001_exam.pdf")
            'abc123_exam.pdf'
            
        Note:
            Like anonymize_filename(), this method checks all known anonymous
            IDs to find matches anywhere within the filename.
        """
        # Try to find and replace any known anonymous ID in the filename
        for anon_id, student_id in self.anon_to_student.items():
            if anon_id in filename:
                return filename.replace(anon_id, student_id)
        
        # If no match found, check if filename starts with an unknown ID
        # This helps catch cases where the anonymous ID isn't in our mapping
        filename_parts = filename.split('_')
        if filename_parts and filename_parts[0] not in self.anon_to_student:
            raise ValueError(f"Filename '{filename}' appears to contain unmapped anonymous ID: {filename_parts[0]}")
        return filename