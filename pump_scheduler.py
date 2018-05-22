#!/usr/bin/python
# Use Python 3

import csv
from datetime import datetime


def extract_time_windows_for_day(schedule_row):
    window_cnt = int((len(schedule_row) - 1) / 2)
    print("Found {} time windows for {}".format(window_cnt, schedule_row[0]))
    result = []
    for window_i in range(1, window_cnt + 1):
        window = [schedule_row[2 * (window_i - 1) + 1], schedule_row[2 * (window_i - 1) + 2]]
        result.append(window)

    return result


def read_schedule(schedule_filepath):
    """Read schedule from CSV file without (!) a header"""
    try:
        schedule_arr = []
        with open(schedule_filepath) as schedule_file:
            schedreader = csv.reader(schedule_file, delimiter=',')
            # next(schedreader)  # Skip header
            # print("Rows read:")
            for row in schedreader:
                # print(row)
                schedule_arr.append(row)
            print("Successfully read schedule from CSV.")
    except IOError as err:
        print("IOError: could not read schedule.csv. {}".format(err))

    # Check schedule for integrity
    for row in schedule_arr:

        # Check incomplete windows (odd number of times)
        if len(row) % 2 == 0:
            raise Exception("Inconsistent schedule: A time window must have both start and end time. "
                            "One is missing in {}'s schedule.".format(row[0]))

        time_windows = extract_time_windows_for_day(row)

        # More detailed checks
        for window_i in range(0, len(time_windows)):
            window_start_time = datetime.strptime(time_windows[window_i][0], "%H:%M").time()
            window_end_time = datetime.strptime(time_windows[window_i][1], "%H:%M").time()

            print("Time window ({}/{}) for today, {}: {} until {}"
                  .format(window_i+1, len(time_windows), row[0],
                          time_windows[window_i][0], time_windows[window_i][1]))

            # Check for reversed window boundaries
            if window_start_time > window_end_time:
                raise Exception("Inconsistent schedule: End time of a window cannot be before its start time. "
                                "Found in window number {} for {}'s schedule.".format(window_i+1, row[0]))

            # Check for overlapping time windows
            if window_i > 0:
                prev_window_end_time = datetime.strptime(time_windows[window_i-1][1], "%H:%M").time()
                if prev_window_end_time > window_start_time:
                    raise Exception("Inconsistent schedule: Consecutive windows cannot overlap. "
                                    "Found in window number {} for {}'s schedule.".format(window_i + 1, row[0]))

    return schedule_arr


def is_pump_desired(schedule_filepath):
    """Check if we are within a specified time window of operation for the current weekday"""

    # Read the schedule
    schedule_arr = read_schedule(schedule_filepath)

    # Determine what day of the week it is today
    now = datetime.now()
    weekday = now.isoweekday()-1
    print("Today is {}".format(now.strftime("%A")))

    # Extract the corresponding schedule for this day
    schedule_today = schedule_arr[weekday]

    # Extract the defined time windows for the day
    time_windows_today = extract_time_windows_for_day(schedule_today)

    # Check if we are within one of the time windows
    for window in time_windows_today:

        # Extract start and end time for current window
        window_start_time = datetime.strptime(window[0], "%H:%M").time()
        window_end_time = datetime.strptime(window[1], "%H:%M").time()

        window_start_datetime = datetime.combine(now.date(), window_start_time)
        window_end_datetime = datetime.combine(now.date(), window_end_time)

        print("Today's hours of operation: "
              "{} until {}".format(window_start_time.strftime("%H:%M"), window_end_time.strftime("%H:%M")))
        # print("window_start_datetime, window_end_datetime: ", window_start_datetime, window_end_datetime)

        # Check if we are within the current time window
        if (now >= window_start_datetime) & (now < window_end_datetime):
            # We are within the current time window, return True
            print("We ARE within a time window right now.")
            return True

    # We are not within one of the time windows for today, return False
    print("We are NOT within a time window right now.")
    return False


def main():
    pump_desired = is_pump_desired('schedule.csv')
    print(pump_desired)
    return pump_desired


if __name__ == "__main__":
    main()