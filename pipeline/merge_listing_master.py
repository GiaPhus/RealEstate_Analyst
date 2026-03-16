import pandas as pd
import os

MASTER = "data/listing.csv"
NEW = "data/listing_new.csv"


def run():

    if not os.path.exists(NEW):
        print("No new listings")
        return

    master_df = pd.read_csv(MASTER)
    new_df = pd.read_csv(NEW)

    merged = pd.concat([master_df, new_df])

    merged.drop_duplicates(subset=["listing_id"], inplace=True)

    merged.to_csv(MASTER, index=False)

    os.remove(NEW)

    print("Merge completed")


if __name__ == "__main__":
    run()