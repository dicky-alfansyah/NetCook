[![Deploy to DigitalOcean](https://web-platforms.sfo2.cdn.digitaloceanspaces.com/WWW/Badge%201.svg)](https://www.digitalocean.com/?refcode=58e3b7de1946&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge)

## Konfigurasi :
- Create a runtime.txt file to install the python version on the digitalocean server with the contents of the :
  ```bash
  python-3.11.7 
  ```
- Create a gunicorn_config.py file for the gunicorn configuration with the contents of the :
  ```bash
  bind = "0.0.0.0:8080"
  workers = 2
  timeout = 600
  ```
- Create a Procfile file for the command to run flask on the digitalocean server with the contents of the :
   ```bash
  web: gunicorn --worker-tmp-dir /dev/shm --config gunicorn_config.py app:app 
  ```
- Create a library dependency file requirements.txt with the :
  ```bash
  pip freeze > requirements.txt 
  ```


# Link to the application that has been deployed:
#### https://app2.dn-project.biz.id

### Test the application:
[![Uji Aplikasi](https://drive.usercontent.google.com/download?id=1J4jWSgGCjAsuzvp4lKDZkByXMT2R3Uhk&export=view&authuser=0)]([https://app2.dn-project.biz.id](https://drive.usercontent.google.com/download?id=1J4jWSgGCjAsuzvp4lKDZkByXMT2R3Uhk&export=view&authuser=0))
