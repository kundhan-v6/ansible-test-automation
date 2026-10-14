
FROM jenkins/inbound-agent:jdk21

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python3-venv python3-pip git \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/ci-venv

COPY jenkins-agent/requirements.txt /tmp/ci-requirements.txt

RUN /opt/ci-venv/bin/pip install --no-cache-dir \
    -r /tmp/ci-requirements.txt \
    && rm /tmp/ci-requirements.txt

ENV PATH="/opt/ci-venv/bin:${PATH}"

COPY requirements.yml /tmp/ansible-requirements.yml

RUN ansible-galaxy collection install \
    -r /tmp/ansible-requirements.yml \
    -p /opt/ansible-collections \
    && rm /tmp/ansible-requirements.yml

ENV ANSIBLE_COLLECTIONS_PATH="/opt/ansible-collections"

USER jenkins
