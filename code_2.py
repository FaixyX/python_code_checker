from collections import Counter

def find_duplicates(input_list):
    counts = Counter(input_list)
    duplicates = [num for num, count in counts.items() if count > 1]
    duplicate_counts = {num: count for num, count in counts.items() if count > 1}
    return {
        "duplicates": duplicates,
        "counts": duplicate_counts
    }

# Example usage:
if __name__ == "__main__":
    # Test Case 1: Normal case with duplicates
    input_list_1 = [4, 3, 2, 7, 8, 2, 3, 1]
    result_1 = find_duplicates(input_list_1)
    print("Test Case 1:", result_1)