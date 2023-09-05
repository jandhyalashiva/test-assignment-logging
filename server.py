from flask import Flask, render_template, request, redirect, url_for
import re

app = Flask(__name__)

# Define a global variable to store device state information.
device_state = {"ON": 0, "ERR": []}

def process_log_file(log_file):
    device_state['ON'] = 0
    device_state['ERR'] = []

    for line in log_file:
        match = re.search(r'\[(\d+)\] dut: Device State: (\w+)', line.decode('utf-8'))
        if match:
            timestamp = int(match.group(1))
            state = match.group(2)
            if state == 'ON':
                device_state['ON'] += 1
            elif state == 'ERR':
                device_state['ERR'].append(timestamp)



@app.route('/', methods=['GET', 'POST'])
def upload_log():
    if request.method == 'POST':
        log_file = request.files['log_file']
        if log_file:
            # Process the log file and update the device_state dictionary.
            process_log_file(log_file)
            return redirect(url_for('display_result'))
    return render_template('upload.html')

@app.route('/result')
def display_result():
    on_time = device_state['ON']
    err_times = device_state['ERR']
    return render_template('result.html', on_time=on_time, err_times=err_times)

if __name__ == '__main__':
    app.run(debug=True)



