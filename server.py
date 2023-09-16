from flask import Flask, render_template, request, redirect, url_for
import re
from datetime import datetime, timedelta


app = Flask(__name__)

def convert_to_days(timestamp_str):
    try:
        # Split the timestamp into its components
        components = timestamp_str.split(':')
        hours = int(components[0])
        minutes = int(components[1])
        seconds = int(components[2])
        milliseconds = int(components[3])
        
        # Calculate the total seconds, including milliseconds
        total_seconds = (hours * 3600) + (minutes * 60) + seconds + (milliseconds / 1000)
        
        # Calculate the total days
        total_days = total_seconds / 86400  # 86400 seconds in a day
        
        return total_days
    except ValueError:
        # Handle parsing errors (invalid timestamp format)
        return None

def parse_timestamp_with_month_day(timestamp_str):
    try:
        # Parse the timestamp string in the format "Jul 23 15:12:57:599"
        timestamp_parts = timestamp_str.split()
        month = timestamp_parts[0]
        day = int(timestamp_parts[1])
        time_parts = timestamp_parts[2].split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2])
        milliseconds = int(time_parts[3])
        
        # Map month abbreviations to month numbers
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Get the current year and create a datetime object
        current_year = datetime.now().year
        timestamp = datetime(current_year, month_map[month], day, hours, minutes, seconds, milliseconds * 1000)
        
        return timestamp
    except (ValueError, KeyError):
        # Handle parsing errors (invalid timestamp format or month abbreviation)
        return None

def subtract_two_timestamps_with_month_day(timestamp1_str, timestamp2_str):
    # Parse both timestamps
    timestamp1 = parse_timestamp_with_month_day(timestamp1_str)
    timestamp2 = parse_timestamp_with_month_day(timestamp2_str)

    if timestamp1 is None or timestamp2 is None:
        return None

    # Subtract the second timestamp from the first
    time_difference = timestamp1 - timestamp2

    # Format the result as "hh:mm:ss:fff"
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = time_difference.microseconds // 1000
    total_hours = hours + time_difference.days * 24
    result_str = f"{total_hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

    return result_str

def parse_timestamp_with_milliseconds(timestamp_str):
    try:
        # Parse the timestamp string in the format "hh:mm:ss:mm"
        time_parts = timestamp_str.split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2])
        milliseconds = int(time_parts[3])
        return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
    except ValueError:
        # Handle parsing errors (invalid timestamp format)
        return None

def add_two_timestamps_with_milliseconds(timestamp1_str, timestamp2_str):
    # Parse both timestamps
    timestamp1 = parse_timestamp_with_milliseconds(timestamp1_str)
    timestamp2 = parse_timestamp_with_milliseconds(timestamp2_str)

    if timestamp1 is None or timestamp2 is None:
        return None

    # Add the two timestamps together
    new_timestamp = timestamp1 + timestamp2

    # Format the result as "hh:mm:ss:mm"
    hours = new_timestamp.seconds // 3600
    minutes = (new_timestamp.seconds % 3600) // 60
    seconds = new_timestamp.seconds % 60
    milliseconds = new_timestamp.microseconds // 1000
    total_hours = hours + new_timestamp.days * 24
    result_str = f"{total_hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

    return result_str


def parse_log_file(log_file):
    on_duration = '00:00:00:000'
    total_on_timestamp = []
    err_timestamps = []
    
    # Define a regular expression for matching log entries with timestamps and device states
    log_entry_regex = r'(\w+ \w+ \d{2}:\d{2}:\d{2}:\d{3}) \[.*\] dut: Device State: (ON|OFF|ERR)'
    
    with open(log_file, 'r') as file:
        is_device_on = False
        for line in file:
            match = re.search(log_entry_regex, line)
            if match:
                timestamp_str = match.group(1)
                state = match.group(2)
                if state == 'ON' and not is_device_on:
                    start_time = timestamp_str
                    is_device_on = True
                    continue
                elif (state == 'ERR' or state == 'OFF') and is_device_on:
                    stop_time = match.group(1)
                    is_device_on = False
                    on_time = subtract_two_timestamps_with_month_day(stop_time, start_time)
                    on_duration = add_two_timestamps_with_milliseconds(on_duration, on_time)
                    total_on_timestamp.append([start_time, stop_time, on_time, True if state == 'Err' else False])
                if state == 'ERR':
                    err_timestamps.append(timestamp_str)
    return on_duration, err_timestamps, total_on_timestamp

                


@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/result', methods=['POST'])
def result():
    if 'log_file' not in request.files:
        return redirect(url_for('upload_file'))

    log_file = request.files['log_file']
    if log_file.filename == '':
        return redirect(url_for('upload_file'))

    log_file.save('test.log')
    
    on_duration, err_timestamps, total_on_timestamp = parse_log_file('test.log')

    return render_template('result.html', on_duration=on_duration, err_timestamps=err_timestamps, total_on_timestamp=total_on_timestamp, equivalent_day= convert_to_days(on_duration))

if __name__ == '__main__':
    app.run(debug=True)
