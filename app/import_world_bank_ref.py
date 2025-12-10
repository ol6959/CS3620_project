import csv
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Lyo265155!",
    "database": "tunetracker"
}

COUNTRY_CSV = "data/WDICountry.csv"
INDICATOR_CSV = "data/WDISeries.csv"


def import_ref_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # -----------------------
    # Import Countries
    # -----------------------
    print("📌 Importing Countries...")
    countries = 0
    with open(COUNTRY_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['\ufeff"Country Code"'].replace('"', '')
            name = row['Short Name']
            region = row['Region'] or None

            if not code or code == "":
                continue

            cursor.execute("""
                INSERT IGNORE INTO ref_country (country_code, name, region)
                VALUES (%s, %s, %s)
            """, (code, name, region))
            countries += 1

    # -----------------------
    # Import Indicators
    # -----------------------
    print("📌 Importing Indicators...")
    indicators = 0
    with open(INDICATOR_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['\ufeff"Series Code"'].replace('"', '')
            name = row['Indicator Name']

            if not code or not name:
                continue

            cursor.execute("""
                INSERT IGNORE INTO ref_indicator (indicator_code, name)
                VALUES (%s, %s)
            """, (code, name))
            indicators += 1

    conn.commit()
    cursor.close()
    conn.close()

    print("🎉 Reference Import Done!")
    print(f"🏳 Countries: {countries}")
    print(f"📊 Indicators: {indicators}")


if __name__ == "__main__":
    import_ref_tables()

