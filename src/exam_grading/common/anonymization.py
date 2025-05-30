"""Helper functions for anonymizing and de-anonymizing student IDs."""
import pandas as pd
from pathlib import Path
from typing import Dict


class StudentAnonymizer:
    """Handles mapping between student IDs and anonymous IDs."""
    
    def __init__(self, students_csv_path: str):
        """
        Initialize the anonymizer with student data.
        
        Args:
            students_csv_path: Path to students CSV file containing studentID and anonymousID columns
        """
        self.students_csv_path = Path(students_csv_path)
        self.student_to_anon: Dict[str, str] = {}
        self.anon_to_student: Dict[str, str] = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load student ID mappings from CSV file."""
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
        for _, row in students_df.iterrows():
            student_id = str(row['studentID'])
            anon_id = str(row['anonymousID'])
            self.student_to_anon[student_id] = anon_id
            self.anon_to_student[anon_id] = student_id
    
    def anonymize(self, student_id: str) -> str:
        """
        Convert student ID to anonymous ID.
        
        Args:
            student_id: The student's real ID
            
        Returns:
            The anonymous ID
            
        Raises:
            ValueError: If no mapping found for the student ID
        """
        student_id_str = str(student_id)
        if student_id_str not in self.student_to_anon:
            raise ValueError(f"No anonymization mapping found for student ID: {student_id}")
        return self.student_to_anon[student_id_str]
    
    def deanonymize(self, anon_id: str) -> str:
        """
        Convert anonymous ID back to student ID.
        
        Args:
            anon_id: The anonymous ID
            
        Returns:
            The student's real ID
            
        Raises:
            ValueError: If no mapping found for the anonymous ID
        """
        anon_id_str = str(anon_id)
        if anon_id_str not in self.anon_to_student:
            raise ValueError(f"No de-anonymization mapping found for anonymous ID: {anon_id}")
        return self.anon_to_student[anon_id_str]
    
    def anonymize_filename(self, filename: str) -> str:
        """
        Anonymize student IDs in a filename.
        
        Args:
            filename: Original filename containing student ID
            
        Returns:
            Filename with student ID replaced by anonymous ID
            
        Raises:
            ValueError: If filename contains an unmapped student ID
        """
        for student_id, anon_id in self.student_to_anon.items():
            if student_id in filename:
                return filename.replace(student_id, anon_id)
        # Check if filename might contain an unmapped student ID
        # Look for patterns like 'studentid_' at the start of filename
        filename_parts = filename.split('_')
        if filename_parts and filename_parts[0] not in self.student_to_anon:
            raise ValueError(f"Filename '{filename}' appears to contain unmapped student ID: {filename_parts[0]}")
        return filename
    
    def deanonymize_filename(self, filename: str) -> str:
        """
        Restore student IDs in a filename.
        
        Args:
            filename: Filename containing anonymous ID
            
        Returns:
            Filename with anonymous ID replaced by student ID
            
        Raises:
            ValueError: If filename contains an unmapped anonymous ID
        """
        for anon_id, student_id in self.anon_to_student.items():
            if anon_id in filename:
                return filename.replace(anon_id, student_id)
        # Check if filename might contain an unmapped anonymous ID
        # Look for patterns like 'anonid_' at the start of filename
        filename_parts = filename.split('_')
        if filename_parts and filename_parts[0] not in self.anon_to_student:
            raise ValueError(f"Filename '{filename}' appears to contain unmapped anonymous ID: {filename_parts[0]}")
        return filename