FROM neosmemo/memos:26.11.0

# Keep the persistent location correct even if the startup command changes.
ENV MEMOS_DATA="/data" \
    MEMOS_PORT="5230"

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose port
EXPOSE 5230

# The upstream image already defines an ENTRYPOINT that starts Memos. Using
# CMD here would only pass /run.sh to that entrypoint as an argument, leaving
# Memos on its non-Supervisor-managed /var/opt/memos volume.
ENTRYPOINT ["/run.sh"]
