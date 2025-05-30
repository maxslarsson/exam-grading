"""Roman numeral conversion utilities for exam grading package.

This module provides bidirectional conversion between Roman numerals and integers,
used primarily for subquestion labeling (i, ii, iii, etc.) in the exam system.
"""


def convert_roman_to_int(roman: str) -> int:
    """Convert a Roman numeral string to an integer.
    
    This function handles standard Roman numerals including subtractive notation
    (e.g., IV for 4, IX for 9). Input is case-insensitive and whitespace is
    stripped automatically.
    
    Args:
        roman: Roman numeral string (e.g., "XIV", "iv", "MCMXCIV")
        
    Returns:
        Integer value of the Roman numeral
        
    Raises:
        ValueError: If the string contains invalid Roman numeral characters
        
    Examples:
        >>> convert_roman_to_int("XIV")
        14
        >>> convert_roman_to_int("iv")
        4
        >>> convert_roman_to_int("MCMXCIV")
        1994
        
    Note:
        Empty strings return 0. The function uses the subtractive principle
        where a smaller numeral before a larger one is subtracted (e.g., IV = 4).
    """
    # Normalize input: strip whitespace and convert to uppercase
    roman = roman.strip().upper()

    # Check if the input is empty
    if not roman:
        return 0
    
    # Define mapping of Roman numerals to integers
    roman_numerals = {
        "I" : 1,
        "V" : 5,
        "X" : 10,
        "L" : 50,
        "C" : 100,
        "D" : 500,
        "M" : 1000
    }

    int_value = 0

    # Process each character in the Roman numeral
    for i in range(len(roman)):
        if roman[i] in roman_numerals:
            # Check for subtractive notation (smaller value before larger)
            if i + 1 < len(roman) and roman_numerals[roman[i]] < roman_numerals[roman[i + 1]]:
                # Subtract this value (e.g., I before V means subtract 1)
                int_value -= roman_numerals[roman[i]]
            else:
                # Add this value normally
                int_value += roman_numerals[roman[i]]
        else:
            raise ValueError(f"Invalid Roman numeral character: {roman[i]}")
    
    return int_value


def convert_int_to_roman(num: int) -> str:
    """Convert an integer to a lowercase Roman numeral string.
    
    This function converts positive integers to their Roman numeral representation
    using standard notation including subtractive pairs (IV, IX, XL, XC, CD, CM).
    The output is in lowercase to match the exam system's subquestion format.
    
    Args:
        num: Positive integer to convert (typically 1-3999)
        
    Returns:
        Lowercase Roman numeral string
        
    Raises:
        ValueError: If input is not a positive integer
        
    Examples:
        >>> convert_int_to_roman(14)
        'xiv'
        >>> convert_int_to_roman(4)
        'iv'
        >>> convert_int_to_roman(1994)
        'mcmxciv'
        
    Note:
        The function returns lowercase Roman numerals to match the convention
        used in exam subquestions (i, ii, iii rather than I, II, III).
    """
    if not isinstance(num, int) or num <= 0:
        raise ValueError("Input must be a positive integer")
    
    # Define Roman numerals in descending order of value
    # Include subtractive pairs for proper notation
    roman_numerals = [
        ("M", 1000),   # 1000
        ("CM", 900),   # 900 (1000 - 100)
        ("D", 500),    # 500
        ("CD", 400),   # 400 (500 - 100)
        ("C", 100),    # 100
        ("XC", 90),    # 90 (100 - 10)
        ("L", 50),     # 50
        ("XL", 40),    # 40 (50 - 10)
        ("X", 10),     # 10
        ("IX", 9),     # 9 (10 - 1)
        ("V", 5),      # 5
        ("IV", 4),     # 4 (5 - 1)
        ("I", 1)       # 1
    ]
    
    result = []
    
    # Build Roman numeral by subtracting largest possible values
    for roman, value in roman_numerals:
        while num >= value:
            result.append(roman)
            num -= value
    
    # Return lowercase for exam system compatibility
    return ''.join(result).lower()
