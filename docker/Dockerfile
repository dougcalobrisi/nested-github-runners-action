# hadolint ignore=DL3007
FROM dougcalobrisi/nested-github-runner-base:latest
LABEL maintainer="doug@calobrisi.com"

ENV AGENT_TOOLSDIRECTORY=/opt/hostedtoolcache
RUN mkdir -p /opt/hostedtoolcache

ARG GH_RUNNER_VERSION="2.289.1"
ARG TARGETPLATFORM

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /actions-runner
COPY install_actions.sh /actions-runner

# TODO: remove this terrible sed once
#  https://github.com/actions/runner/pull/1585 is merged or similar
RUN chmod +x /actions-runner/install_actions.sh \
  && sed -i.bak 's/.\/bin\/installdependencies.sh/wget https:\/\/raw.githubusercontent.com\/myoung34\/runner\/main\/src\/Misc\/layoutbin\/installdependencies.sh -O .\/bin\/installdependencies.sh; bash .\/bin\/installdependencies.sh/g' /actions-runner/install_actions.sh \
  && /actions-runner/install_actions.sh ${GH_RUNNER_VERSION} ${TARGETPLATFORM} \
  && rm /actions-runner/install_actions.sh \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY token.sh entrypoint.sh ephemeral-runner.sh /
RUN chmod +x /token.sh /entrypoint.sh /ephemeral-runner.sh
 
RUN groupadd -g 121 runner && useradd -mr -d /home/runner -u 1001 -g 121 runner \
  && echo "runner ALL= EXEC: NOPASSWD:ALL" >> /etc/sudoers.d/runner \
  && chown -R runner.runner /_work/ && chown -R runner.runner /opt/hostedtoolcache/

WORKDIR /home/runner
USER runner
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/actions-runner/bin/Runner.Listener", "run", "--startuptype", "service"]
