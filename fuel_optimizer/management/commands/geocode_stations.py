import pandas as pd
from django.core.management.base import BaseCommand, CommandParser
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import ArcGIS
from tqdm import tqdm

from fuel_optimizer.models import FuelStation


class Command(BaseCommand):
    help = "One-time geocoding of all fuel stations"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        geocoder = ArcGIS(timeout=10)
        geocode = RateLimiter(geocoder.geocode, min_delay_seconds=1, max_retries=3)

        self.stdout.write(f"Loading fuel stations from: {csv_file}")

        try:
            df = pd.read_csv(csv_file)
        except FileNotFoundError:
            self.stderr.write(f"File not found: {csv_file}")
            return
        except Exception as e:
            self.stderr.write(f"Failed to parse file: {str(e)}")
            return

        df.rename(
            columns=lambda col: col.strip().lower().replace(" ", "_"), inplace=True
        )

        # Skip existing stations
        csv_ids = df["opis_truckstop_id"].tolist()
        existing_ids = set(
            FuelStation.objects.filter(opis_id__in=csv_ids).values_list(
                "opis_id", flat=True
            )
        )
        initial_count = len(df)
        df = df[~df["opis_truckstop_id"].isin(existing_ids)]

        self.stdout.write(f"Skipping {initial_count - len(df)} existing stations")
        self.stdout.write(f"Processing {len(df)} new fuel stations...")

        if len(df) == 0:
            self.stdout.write("No new stations to process!")
            return

        geocoded_count = 0
        failed_count = 0

        for idx, row in tqdm(
            df.iterrows(), total=len(df), desc="Geocoding new stations"
        ):
            try:
                opis_id = int(row["opis_truckstop_id"])
                address = f"{row['city']}, {row['state']}, USA"
                location = geocode(address, timeout=10)

                if location:
                    FuelStation.objects.get_or_create(
                        opis_id=opis_id,
                        name=row["truckstop_name"].strip(),
                        city=row["city"].strip(),
                        state=row["state"].strip().upper(),
                        retail_price=float(row["retail_price"]),
                        latitude=location.latitude,
                        longitude=location.longitude,
                    )
                    geocoded_count += 1
                else:
                    failed_count += 1

            except (GeocoderTimedOut, GeocoderServiceError):
                failed_count += 1
                self.stderr.write(
                    f"[{failed_count}] Geocoder error on row {idx} (ID={opis_id}, address='{address}'): {e}"
                )
            except Exception:
                failed_count += 1
                self.stderr.write(
                    f"[{failed_count}] Unexpected error on row {idx} (ID={opis_id}, address='{address}'): {e}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Geocoding complete! Created: {geocoded_count}, Failed: {failed_count}"
            )
        )
