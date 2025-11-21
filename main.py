"""
@file main.py
@brief Complete analytical client for API (timeline + tickets analytics).

This module performs all required API calls, processes the data, builds
analytical visualizations, and saves results into files.

@note Built according to assignment requirements:
      - Line chart (tickets per day, last 30 days)
      - Bar chart (tickets by hour of day)
      - Heatmap (activity by weekday & hour)
      - Pie chart (tickets by category)
      - Horizontal bar chart (avg resolution time by category)
      - CSV table (top-5 categories by ticket count)
"""

# CONSTANTS

BASE_URL = "http://193.233.171.205:5000"

# API endpoints
ENDPOINT_TIMELINE = "/api/v1/timeline"
ENDPOINT_TICKETS = "/api/v1/tickets"
ENDPOINT_TICKET = "/api/v1/tickets/"  # + ticket_id

# Output directory
OUTPUT_DIR = "output/"

# Authentication
LOGIN = "analyst_di"
CODE = "LmN23vWx45Qr"

# IMPORTS

import os
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

os.makedirs(OUTPUT_DIR, exist_ok=True)

# API FUNCTIONS

def make_request(endpoint, params=None):
    """
    @brief Perform authenticated GET request to API.
    @param endpoint (str): API endpoint such as '/api/v1/tickets'
    @param params (dict): Additional query parameters
    @return JSON response dictionary

    @throws requests.exceptions.RequestException on network/API error
    """
    if params is None:
        params = {}

    params["login"] = LOGIN
    params["code"] = CODE

    url = BASE_URL + endpoint
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_timeline(days=30):
    """
    @brief Get timeline data for the past N days.
    @param days (int): Number of days.
    @return dict containing timeline entries.
    """
    return make_request(ENDPOINT_TIMELINE, params={"days": days})


def get_tickets():
    """
    @brief Get all tickets assigned to the analyst.
    @return list of tickets.
    """
    return make_request(ENDPOINT_TICKETS)

# DATA PROCESSING

def preprocess_tickets(tickets):
    """
    @brief Convert raw ticket JSON list to dataframe with derived columns.
    @param tickets (list): List of ticket dicts.
    @return pandas.DataFrame with parsed fields.
    """
    df = pd.DataFrame(tickets)

    # Convert timestamps
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["created_hour"] = df["created_at"].dt.hour
    df["weekday"] = df["created_at"].dt.day_name()

    # Resolution time (hours)
    df["closed_at"] = pd.to_datetime(df["closed_at"], errors="coerce")
    df["resolution_hours"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 3600

    return df


def save_line_chart_timeline(df):
    """
    @brief Save line chart of created tickets over time (30 days).
    """
    plt.figure(figsize=(12, 5))
    plt.plot(df["date"], df["tickets_created"], marker="o", label="Created")
    plt.plot(df["date"], df["tickets_resolved"], marker="o", label="Resolved")
    plt.title("Tickets Timeline (Last 30 Days)")
    plt.xlabel("Date")
    plt.ylabel("Count")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    path = OUTPUT_DIR + "timeline_linechart.png"
    plt.savefig(path)
    print("[OK] Saved:", path)
    plt.close()


def save_bar_by_hour(df):
    """
    @brief Save bar chart of ticket creation by hour of day.
    """

    # Count tickets by hour
    hourly = df.groupby("created_hour").size()
    hourly = hourly.reindex(range(24), fill_value=0)

    plt.figure(figsize=(12, 5))
    hourly.plot(kind="bar", color="purple")

    plt.title("Tickets by Hour of Day")
    plt.xlabel("Hour")
    plt.ylabel("Number of Tickets")
    plt.xticks(range(24), range(24))

    plt.tight_layout()
    path = OUTPUT_DIR + "tickets_by_hour.png"
    plt.savefig(path)
    plt.close()

    print("[OK] Saved:", path)


def save_heatmap(df):
    """
    @brief Save weekday-hour heatmap of ticket activity.
    """

    # Build table
    pivot = df.pivot_table(
        index="weekday",
        columns="created_hour",
        values="ticket_id",
        aggfunc="count",
        fill_value=0
    )
    pivot = pivot.reindex(columns=range(24), fill_value=0)
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(weekday_order)

    plt.figure(figsize=(18, 6))
    sns.heatmap(pivot, cmap="Purples", linewidths=0.5)

    plt.title("Activity Heatmap (Weekday × Hour)")
    plt.xlabel("Hour")
    plt.ylabel("Weekday")
    plt.xticks(ticks=np.arange(24) + 0.5, labels=list(range(24)), rotation=0)

    plt.tight_layout()
    path = OUTPUT_DIR + "heatmap_weekday_hour.png"
    plt.savefig(path)
    plt.close()

    print("[OK] Saved:", path)


def save_pie_categories(df):
    """
    @brief Save pie chart of ticket categories.
    """
    cat_counts = df["category_name"].value_counts()

    plt.figure(figsize=(8, 8))
    plt.pie(cat_counts, labels=cat_counts.index, autopct="%1.1f%%")
    plt.title("Ticket Distribution by Category")
    plt.tight_layout()
    path = OUTPUT_DIR + "pie_categories.png"
    plt.savefig(path)
    print("[OK] Saved:", path)
    plt.close()


# def save_resolution_bar(df):
#     """
#     @brief Save horizontal bar chart of average resolution time per category.
#     """
#     resolved = df.dropna(subset=["resolution_hours"])
#     avg_res = resolved.groupby("category_name")["resolution_hours"].mean().sort_values()

#     plt.figure(figsize=(10, 6))
#     avg_res.plot(kind="barh", color="purple")
#     plt.title("Average Resolution Time (Hours) by Category")
#     plt.xlabel("Hours")
#     plt.tight_layout()
#     path = OUTPUT_DIR + "resolution_time_by_category.png"
#     plt.savefig(path)
#     print("[OK] Saved:", path)
#     plt.close()

def save_resolution_bar(df):
    """
    @brief Save horizontal bar chart of average resolution time per category.
    """

    resolved = df.dropna(subset=["resolution_hours"])
    avg_res = resolved.groupby("category_name")["resolution_hours"].mean()
    all_categories = df["category_name"].unique()
    avg_res = avg_res.reindex(all_categories)
    avg_res_filled = avg_res.fillna(0)

    plt.figure(figsize=(10, 6))
    avg_res_filled.sort_values().plot(kind="barh", color="purple")

    plt.title("Average Resolution Time (Hours) by Category")
    plt.xlabel("Hours")

    for idx, value in enumerate(avg_res_filled.sort_values()):
        if value == 0:
            plt.text(0.1, idx, "no data", va="center", color="red")

    plt.tight_layout()
    path = OUTPUT_DIR + "resolution_time_by_category.png"
    plt.savefig(path)
    plt.close()

    print("[OK] Saved:", path)


def save_top5_categories_csv(df):
    """
    @brief Save CSV of top-5 categories by ticket count.
    """
    top5 = df["category_name"].value_counts().head(5).reset_index()
    top5.columns = ["Category", "Count"]
    path = OUTPUT_DIR + "top5_categories.xlsx"
    top5.to_excel(path, index=False)
    print("[OK] table saved:", path)


def save_timeline_comparison():
    """
    @brief Build comparison plot of department workload for 7, 14 and 30 days.
    """

    # Load raw data
    data_7  = get_timeline(7)
    data_14 = get_timeline(14)
    data_30 = get_timeline(30)

    df7  = pd.DataFrame(data_7["data"])
    df14 = pd.DataFrame(data_14["data"])
    df30 = pd.DataFrame(data_30["data"])

    df7["date"]  = pd.to_datetime(df7["date"])
    df14["date"] = pd.to_datetime(df14["date"])
    df30["date"] = pd.to_datetime(df30["date"])

    full_range = pd.date_range(df30["date"].min(), df30["date"].max())

    # Reindex all frames to the same date range
    df7 = df7.set_index("date").reindex(full_range, fill_value=0).rename_axis("date")
    df14 = df14.set_index("date").reindex(full_range, fill_value=0).rename_axis("date")
    df30 = df30.set_index("date").reindex(full_range, fill_value=0).rename_axis("date")

    plt.figure(figsize=(14, 6))
    plt.plot(df7.index, df7["tickets_created"], marker="o", label="7 days")
    plt.plot(df14.index, df14["tickets_created"], marker="o", label="14 days")
    plt.plot(df30.index, df30["tickets_created"], marker="o", label="30 days")

    plt.title("Workload Growth: 7 / 14 / 30 Days")
    plt.xlabel("Date")
    plt.ylabel("Tickets Created")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    path = OUTPUT_DIR + "workload_7_14_30.png"
    plt.savefig(path)
    plt.close()

    print("[OK] Saved:", path)


def print_workload_summary():
    """
    @brief Print analytical summary for workload over 7, 14, 30 days.
    """

    # Load timeline for different periods
    data_7 = get_timeline(7)
    data_14 = get_timeline(14)
    data_30 = get_timeline(30)

    df7 = pd.DataFrame(data_7["data"])
    df14 = pd.DataFrame(data_14["data"])
    df30 = pd.DataFrame(data_30["data"])

    df7["tickets_created"] = df7["tickets_created"].astype(int)
    df14["tickets_created"] = df14["tickets_created"].astype(int)
    df30["tickets_created"] = df30["tickets_created"].astype(int)

    # Totals
    total_7 = df7["tickets_created"].sum()
    total_14 = df14["tickets_created"].sum()
    total_30 = df30["tickets_created"].sum()

    # Averages
    avg_7 = df7["tickets_created"].mean()
    avg_14 = df14["tickets_created"].mean()
    avg_30 = df30["tickets_created"].mean()

    # Percent changes
    def pct_change(a, b):
        if a == 0:
            return float("nan")
        return (b - a) / a * 100

    change_7_to_14 = pct_change(total_7, total_14)
    change_14_to_30 = pct_change(total_14, total_30)

    print("\n==============================")
    print(" WORKLOAD ANALYTICAL SUMMARY")
    print("==============================")

    print(f"Total tickets created in last 7 days:  {total_7}")
    print(f"Total tickets created in last 14 days: {total_14}")
    print(f"Total tickets created in last 30 days: {total_30}\n")

    print(f"Average tickets/day (7 days):  {avg_7:.2f}")
    print(f"Average tickets/day (14 days): {avg_14:.2f}")
    print(f"Average tickets/day (30 days): {avg_30:.2f}\n")

    print(f"Change 7-14 days:  {change_7_to_14:.1f}%")
    print(f"Change 14-30 days: {change_14_to_30:.1f}%\n")


def main():
    """
    @brief Execute the complete analytical workflow and print summary statistics.
    @return None
    """

    print("\n==============================")
    print("1) Downloading timeline data")
    print("==============================")

    # 1) Timeline 30 days
    timeline_raw = get_timeline(30)
    timeline_df = pd.DataFrame(timeline_raw["data"])
    timeline_df["date"] = pd.to_datetime(timeline_df["date"])
    save_line_chart_timeline(timeline_df)

    # Console summary
    total_created_30 = timeline_df["tickets_created"].sum()
    total_resolved_30 = timeline_df["tickets_resolved"].sum()
    print(f"Total tickets created in last 30 days: {total_created_30}")
    print(f"Total tickets resolved in last 30 days: {total_resolved_30}")

    print("\n==============================")
    print("2) Downloading tickets data")
    print("==============================")

    # 2) Tickets
    tickets_raw = get_tickets()
    tickets_df = preprocess_tickets(tickets_raw)

    total_tickets = len(tickets_df)
    categories_count = tickets_df["category_name"].nunique()
    print(f"Total tickets assigned: {total_tickets}")
    print(f"Unique categories: {categories_count}")

    # Peak hour
    peak_hour = tickets_df["created_hour"].mode()[0]
    print(f"Most active hour: {peak_hour}:00")

    # Peak weekday
    peak_weekday = tickets_df["weekday"].mode()[0]
    print(f"Most active weekday: {peak_weekday}")

    print("\n==============================")
    print("3) Running analytics & saving plots")
    print("==============================")

    save_bar_by_hour(tickets_df)
    save_heatmap(tickets_df)
    save_pie_categories(tickets_df)
    save_resolution_bar(tickets_df)
    save_top5_categories_csv(tickets_df)
    save_timeline_comparison()
    print("\n==============================")
    print("4) Statistics")
    print("==============================")

    # Top-5 categories
    top5 = tickets_df["category_name"].value_counts().head(5)
    print("\nTop-5 categories by number of tickets:")
    print(top5.to_string())

    # Average resolution time
    resolved = tickets_df.dropna(subset=["resolution_hours"])
    avg_res = resolved.groupby("category_name")["resolution_hours"].mean().sort_values()

    print("\nAverage resolution time (hours) by category:")
    print(avg_res.to_string())
    print_workload_summary()

    print("\n==============================")
    print("Completed successfully ")
    print("==============================\n")

if __name__ == "__main__":
    main()
