ARG SUPERSET_TAG=4.1.1
FROM apache/superset:${SUPERSET_TAG}

USER root
RUN pip install --no-cache-dir psycopg2-binary
COPY superset_config.py /app/pythonpath/superset_config.py
COPY init.sh /app/init.sh
RUN chmod +x /app/init.sh
USER superset

CMD ["/app/init.sh"]
