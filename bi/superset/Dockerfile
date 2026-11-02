FROM apache/superset:4.1.2
USER root
RUN pip install --no-cache-dir psycopg2-binary flask-cors
COPY bi/superset/superset_config.py /app/pythonpath/superset_config.py
COPY bi/superset/init.sh /usr/local/bin/superset-init.sh
RUN chmod +x /usr/local/bin/superset-init.sh
USER superset
EXPOSE 8088
ENTRYPOINT ["/usr/local/bin/superset-init.sh"]
