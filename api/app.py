import os
import uuid
import time
import json
import shutil
import zipfile
import requests
import threading
import pandas as pd
from myurls import netflix_url
from patoolib import extract_archive
from flask import Flask, render_template, request, send_file, session

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

TEMP_FOLDER = '/tmp'

def generate_unique_id():
    return str(uuid.uuid4())

def create_temp_directory():
    if 'temp_id' not in session:
        session['temp_id'] = generate_unique_id()
    temp_dir = get_temp_directory(session['temp_id'])
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

def delete_temp_directory(temp_id):
    temp_dir = get_temp_directory(temp_id)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def get_temp_directory(temp_id):
    return os.path.join(TEMP_FOLDER, temp_id)

def check_cookies_valid_netflix(cookies):
    response = requests.get(netflix_url, cookies=cookies, allow_redirects=False)
    return "Active" if response.status_code == 200 else "Expired"

def read_cookies(file):
    cookies = {}
    if file.endswith('.json'):
        with open(file, 'r') as f:
            cookies_json = json.load(f)
            for cookie in cookies_json:
                if 'name' in cookie and 'value' in cookie:
                    name = cookie.get('name')
                    value = cookie.get('value')
                    cookies[name] = value
    elif file.endswith('.txt'):
        with open(file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    name = parts[5]
                    value = parts[6]
                    cookies[name] = value
    return cookies

def process_uploaded_file(file_path, temp_id):
    if file_path.endswith('.zip'):
        return extract_and_process_cookies_zip(file_path, temp_id)
    elif file_path.endswith(('.txt', '.json')):
        return extract_and_process_cookies_single(file_path, temp_id)
    else:
        return pd.DataFrame()

def extract_and_process_cookies_zip(file_path, temp_id):
    result_df = pd.DataFrame(columns=['File Name', 'Cookies Status'])
    temp_folder = get_temp_directory(temp_id)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_folder)

    extracted_files = [f for f in os.listdir(temp_folder) if os.path.isfile(os.path.join(temp_folder, f))]
    extracted_files = extracted_files[:26]

    for file_name in extracted_files:
        if file_name.endswith('.txt') or file_name.endswith('.json'):
            file_path = os.path.join(temp_folder, file_name)
            cookies = read_cookies(file_path)
            cookies_status = check_cookies_valid_netflix(cookies)
            temp_df = pd.DataFrame({'File Name': [file_name], 'Cookies Status': [cookies_status]})
            result_df = pd.concat([result_df, temp_df], ignore_index=True)
    return result_df

def extract_and_process_cookies_single(file_path, temp_id):
    file_name = os.path.basename(file_path)
    cookies = read_cookies(file_path)
    cookies_status = check_cookies_valid_netflix(cookies)
    result_df = pd.DataFrame({'File Name': [file_name], 'Cookies Status': [cookies_status]})
    return result_df

def delete_temp_directory_after_delay(temp_id, delay):
    while True:
        time.sleep(delay)
        delete_temp_directory(temp_id)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file uploaded!')

        file = request.files['file']

        if file.filename == '':
            return render_template('index.html', error='No file uploaded!')

        allowed_formats = ['.txt', '.json', '.zip']
        if not any(file.filename.endswith(format) for format in allowed_formats):
            return render_template('index.html', error='Invalid file format!')

        create_temp_directory()
        temp_dir = get_temp_directory(session['temp_id'])
        delete_temp_directory(session['temp_id'])
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        delay = 3600
        threading.Thread(target=delete_temp_directory_after_delay, args=(session['temp_id'], delay)).start()

        if file.filename.endswith('.zip'):
            loading()
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                extracted_files = zip_ref.namelist()

            if len(extracted_files) > 25:
                return render_template('index.html', error=' The number of files exceeds the limit!. Make sure the zip file has a maximum of 25 files in it')

            if any('/' in name for name in extracted_files):
                return render_template('index.html', error='Files inside the zip archive must not be contained within a folder!')

            invalid_files = [name for name in extracted_files if not (name.endswith('.txt') or name.endswith('.json'))]
            if invalid_files:
                return render_template('index.html', error=f'Zip files must contain only .txt and .json files!')

            result_df = process_uploaded_file(file_path, session['temp_id'])
            active_cookies_df = result_df[result_df['Cookies Status'] == 'Active']

            if not active_cookies_df.empty:
                active_cookies_df = active_cookies_df.sort_values(by='Cookies Status')
                active_cookies = active_cookies_df.to_dict(orient='records')

                total_files = len(result_df)
                total_active_cookies = len(active_cookies_df)
                total_expired_cookies = total_files - total_active_cookies

                summary = {
                    'Total Files': total_files,
                    'Total Active Cookies': total_active_cookies,
                    'Total Expired Cookies': total_expired_cookies
                }

                return render_template('index.html', active_cookies=active_cookies, summary=summary, temp_id=session['temp_id'])
            else:
                return render_template('index.html', error='No active cookies found!')
        else:
            result_df = process_uploaded_file(file_path, session['temp_id'])
            active_cookies_df = result_df[result_df['Cookies Status'] == 'Active']

            if not active_cookies_df.empty:
                active_cookies_df = active_cookies_df.sort_values(by='Cookies Status')
                active_cookies = active_cookies_df.to_dict(orient='records')

                total_files = len(result_df)
                total_active_cookies = len(active_cookies_df)
                total_expired_cookies = total_files - total_active_cookies

                summary = {
                    'Total Files': total_files,
                    'Total Active Cookies': total_active_cookies,
                    'Total Expired Cookies': total_expired_cookies
                }

                return render_template('index.html', active_cookies=active_cookies, summary=summary, temp_id=session['temp_id'])
            else:
                return render_template('index.html', error='No active cookies found!')

    return render_template('index.html', summary=None)

@app.route('/download/<file_name>', methods=['GET'])
def download_file(file_name):
    temp_dir = get_temp_directory(session['temp_id'])
    file_path = os.path.join(temp_dir, file_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

def loading():
    pass

if __name__ == '__main__':
    app.run(debug=False)
