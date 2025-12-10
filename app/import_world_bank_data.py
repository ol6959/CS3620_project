import csv
import mysql.connector

DB = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD",
    "database": "tunetracker"
}

WDI_DATA = "data/WDIData.csv"
COMMIT_EVERY = 1000

INDICATORS = {
    "NY.GDP.PCAP.KD",  # GDP per capita (constant 2015 USD)
    "IT.NET.USER.ZS"   # Individuals using the Internet (% of population)
}

def import_indicator_values():
    conn = mysql.connector.connect(**DB)
    cursor = conn.cursor()

    print("📊 Importing World Bank Indicator Data...")

    with open(WDI_DATA, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        processed = 0
        inserted = 0

        for row in reader:
            processed += 1

            indicator_code = row["Indicator Code"]
            if indicator_code not in INDICATORS:
                continue

            country_code = row["Country Code"].strip()

            # Loop across years present in this row
            for key, value in row.items():
                # Skip non-year fields + empty column
                if not key.isdigit():
                    continue
                if value in ("", None):
                    continue

                try:
                    year = int(key)
                    val = float(value)
                except:
                    continue  # Skip invalid numbers

                cursor.execute("""
                    INSERT INTO bg_country_indicator
                        (country_code, indicator_code, year, value)
                    VALUES (%s, %s, %s, %s)
                """, (country_code, indicator_code, year, val))

                inserted += 1

            if processed % COMMIT_EVERY == 0:
                conn.commit()
                print(f"💾 Committed {processed:,} rows...")

    conn.commit()
    cursor.close()
    conn.close()

    print("🎉 Done importing indicator data!")
    print(f"Processed rows: {processed:,}")
    print(f"Values inserted: {inserted:,}")


if __name__ == "__main__":
    import_indicator_values()

