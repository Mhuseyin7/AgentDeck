FROM alpine:3.20
RUN adduser -D -u 10001 agent
COPY fake-agent /usr/local/bin/fake-agent
RUN chmod 0555 /usr/local/bin/fake-agent
USER 10001
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/fake-agent"]
