"""Progress reporting utilities for exam grading package.

This module provides a simple progress tracking utility for console applications,
giving users feedback during long-running operations like file processing,
uploads, and downloads.
"""


class ProgressPrinter:
    """Simple progress printer for console output.
    
    This class provides a lightweight progress indicator that updates in-place
    on the console using carriage returns. It's designed for tracking progress
    through batch operations where you know the total count upfront.
    
    Attributes:
        task_name: Description of the task being performed
        total: Total number of items to process
        
    Example:
        >>> progress = ProgressPrinter("Processing files", 100)
        >>> for i in range(100):
        ...     # Do some work
        ...     progress.update(i + 1)
        >>> progress.done()
        Processing files...Done!
    """
    
    def __init__(self, task_name: str, total: int):
        """Initialize progress printer.
        
        Args:
            task_name: Name of the task being tracked (e.g., "Uploading PDFs")
            total: Total number of items to process
        """
        self.task_name = task_name
        self.total = total
    
    def update(self, current: int) -> None:
        """Update progress display with current status.
        
        This method updates the console display in-place using a carriage return,
        showing the current progress as "Task...X/Y" where X is the current item
        and Y is the total.
        
        Args:
            current: Current item number (1-based, not 0-based)
            
        Note:
            The carriage return (\\r) allows updating the same line repeatedly
            without scrolling. The flush=True ensures immediate display.
        """
        print(f"{self.task_name}...{current}/{self.total}", end='\r', flush=True)
    
    def done(self) -> None:
        """Mark task as complete and finalize the display.
        
        This method prints the final "Done!" message and adds spaces to clear
        any remaining characters from the progress counter. A newline is
        implicit in the print statement, moving the cursor to the next line.
        """
        print(f"{self.task_name}...Done!    ")  # Extra spaces clear any remaining digits