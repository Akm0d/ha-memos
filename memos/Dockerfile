ARG BUILD_FROM
FROM neosmemo/memos:0.24.0

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose port
EXPOSE 5230

CMD ["/run.sh"]
