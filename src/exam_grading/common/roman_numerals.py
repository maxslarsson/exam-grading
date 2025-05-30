def convert_roman_to_int(roman: str) -> int:
    """
    Convert a Roman numeral to an integer.
    
    Args:
        roman (str): Roman numeral string.
        
    Returns:
        int: Integer value of the Roman numeral.
    """
    roman = roman.strip().upper()  # Normalize input: strip whitespace and convert to uppercase

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

    for i in range(len(roman)):
        if roman[i] in roman_numerals:
            if i + 1 < len(roman) and roman_numerals[roman[i]] < roman_numerals[roman[i + 1]]:
                int_value -= roman_numerals[roman[i]]
            else:
                int_value += roman_numerals[roman[i]]
        else:
            raise ValueError(f"Invalid Roman numeral character: {roman[i]}")
    
    return int_value


def convert_int_to_roman(num: int) -> str:
    """
    Convert an integer to a Roman numeral.
    
    Args:
        num (int): Integer value to convert.
        
    Returns:
        str: Roman numeral representation of the integer.
    """
    if not isinstance(num, int) or num <= 0:
        raise ValueError("Input must be a positive integer")
    
    roman_numerals = [
        ("M", 1000),
        ("CM", 900),
        ("D", 500),
        ("CD", 400),
        ("C", 100),
        ("XC", 90),
        ("L", 50),
        ("XL", 40),
        ("X", 10),
        ("IX", 9),
        ("V", 5),
        ("IV", 4),
        ("I", 1)
    ]
    
    result = []
    
    for roman, value in roman_numerals:
        while num >= value:
            result.append(roman)
            num -= value
    
    return ''.join(result).lower()
