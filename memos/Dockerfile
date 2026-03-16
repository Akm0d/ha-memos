ARG BUILD_FROM
FROM neosmemo/memos:0.24.0

# Set data directory to HA config location
ENV MEMOS_DATA=/config/memos
ENV MEMOS_MODE=prod
ENV MEMOS_PORT=5230

# Create data directory
RUN mkdir -p /config/memos

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose port
EXPOSE 5230

CMD ["/run.sh"]
