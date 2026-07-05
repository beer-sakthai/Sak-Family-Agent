import argparse
import pandas as pd
import io

def perform_eda(csv_path: str):
    """
    Performs a basic Exploratory Data Analysis on a given CSV file and prints a report.

    Args:
        csv_path: The file path to the CSV file to be analyzed.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: The file at '{csv_path}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return

    print(f"Exploratory Data Analysis Report for: {csv_path}")
    print("=" * 80)

    # 1. Basic Information
    print("\n1. Basic Information")
    print("-" * 80)
    # Capture df.info() output to a string
    buffer = io.StringIO()
    df.info(buf=buffer)
    print(buffer.getvalue())

    # 2. First 5 Rows (Head)
    print("\n2. First 5 Rows")
    print("-" * 80)
    print(df.head().to_string())

    # 3. Descriptive Statistics for Numerical Columns
    numerical_cols = df.select_dtypes(include=['number'])
    if not numerical_cols.empty:
        print("\n3. Descriptive Statistics (Numerical Columns)")
        print("-" * 80)
        print(numerical_cols.describe().to_string())
    else:
        print("\n3. No numerical columns found for descriptive statistics.")

    # 4. Value Counts for Categorical Columns
    categorical_cols = df.select_dtypes(include=['object', 'category'])
    if not categorical_cols.empty:
        print("\n4. Value Counts (Categorical Columns)")
        print("-" * 80)
        for col in categorical_cols.columns:
            print(f"\n--- Column: {col} ---")
            print(categorical_cols[col].value_counts().to_string())
            print("-" * 20)
    else:
        print("\n4. No categorical columns found for value counts.")

    print("\n" + "=" * 80)
    print("EDA Report Complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Perform Exploratory Data Analysis (EDA) on a CSV file."
    )
    parser.add_argument(
        "csv_path",
        type=str,
        help="The path to the CSV file to analyze."
    )

    args = parser.parse_args()

    # To use this skill, you'll need to have pandas installed.
    # You can add it to your project's dependencies:
    # uv pip install pandas

    perform_eda(args.csv_path)