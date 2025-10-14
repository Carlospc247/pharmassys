#!/bin/bash
# Atualiza pacotes
sudo apt update && sudo apt upgrade -y

# Instala dependências
sudo apt install python3-pip python3-venv nginx git -y

# Cria virtualenv
python3 -m venv /var/www/venv
source /var/www/venv/bin/activate

# Instala requisitos
pip install -r requirements.txt

# Migra banco de dados
python manage.py migrate

# Coleta arquivos estáticos
python manage.py collectstatic --noinput

# Inicia Gunicorn systemd
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Ativa Nginx
sudo ln -s /var/www/pharmassys/nginx/pharmassys.conf /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
