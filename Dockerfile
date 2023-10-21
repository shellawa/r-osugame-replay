# Stage 1: Build the shell script
FROM alpine:3.14 as builder

WORKDIR /build
RUN echo '#!/bin/sh' > restart_script.sh \
    && echo 'while true; do' >> restart_script.sh \
    && echo '    python main.py' >> restart_script.sh \
    && echo '    echo "Restarting the Python script..."' >> restart_script.sh \
    && echo '    sleep 1800' >> restart_script.sh \
    && echo 'done' >> restart_script.sh \
    && chmod +x restart_script.sh

# Stage 2: Build the final image
FROM python:3.8

WORKDIR /app

# Copy your Python script into the container
COPY . /app/

# Copy the shell script from the builder stage
COPY --from=builder /build/restart_script.sh /app/restart_script.sh

# Make the shell script executable
RUN chmod +x /app/restart_script.sh

# Set the entry point to run the shell script
CMD ["/app/restart_script.sh"]