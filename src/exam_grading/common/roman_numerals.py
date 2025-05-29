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
