"""Progress reporting utilities for exam grading package."""


class ProgressPrinter:
    """Simple progress printer for console output."""
    
    def __init__(self, task_name: str, total: int):
        """
        Initialize progress printer.
        
        Args:
            task_name: Name of the task being tracked
            total: Total number of items to process
        """
        self.task_name = task_name
        self.total = total
    
    def update(self, current: int) -> None:
        """
        Update progress display.
        
        Args:
            current: Current item number (1-based)
        """
        print(f"{self.task_name}...{current}/{self.total}", end='\r', flush=True)
    
    def done(self) -> None:
        """Mark task as complete."""
        print(f"{self.task_name}...Done!    ")