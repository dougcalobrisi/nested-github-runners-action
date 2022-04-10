import os
import logging
import sys
import threading
import signal

import docker

docker_client = docker.from_env()

GITHUB_TOKEN = os.environ.get("INPUT_GITHUB_TOKEN")
RUN_ID = os.environ.get("GITHUB_RUN_ID")

RUNNER_QUANTITY = os.environ.get("INPUT_RUNNERS")
DOCKER_RUNNER_IMAGE = os.environ.get("INPUT_RUNNER_IMAGE")
RUNNER_PREFIX = os.environ.get("INPUT_RUNNER_PREFIX")
RUNNER_LABEL = os.environ.get("INPUT_RUNNER_LABEL")

DOCKER_IN_DOCKER = os.environ.get("INPUT_DOCKER_IN_DOCKER")

SHARED_VOLUME_RUNNER_PATH = os.environ.get("INPUT_SHARED_VOLUME")
SHARED_VOLUME_HOST_PATH = os.environ.get("INPUT_SHARED_VOLUME_HOST_PATH")

GITHUB_SERVER_URL = os.environ.get("GITHUB_SERVER_URL")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
GITHUB_REPOSITORY_URL = f"{GITHUB_SERVER_URL}/{GITHUB_REPOSITORY}"
GITHUB_API_URL = os.environ.get("GITHUB_API_URL")

FALSY = ["false", "no", "disable", "disabled", "off"]


def build_volumes_list():
    volumes = []

    if str(DOCKER_IN_DOCKER).lower() not in FALSY:
        volumes.append("/var/run/docker.sock:/var/run/docker.sock")
    else:
        logging.info("Docker-in-Docker disabled by configuration")

    if str(SHARED_VOLUME_RUNNER_PATH).lower() not in FALSY:
        if not os.path.exists(SHARED_VOLUME_HOST_PATH):
            try:
                os.system(f"sudo mkdir -p {SHARED_VOLUME_HOST_PATH}")
                os.system(f"sudo chown runner:runner {SHARED_VOLUME_HOST_PATH}")
            except:
                logging.critical("Failed to create shared volume")
                sys.exit(1)

        shared_volume = f"{SHARED_VOLUME_HOST_PATH}:{SHARED_VOLUME_RUNNER_PATH}"
        volumes.append(shared_volume)
        logging.info(f"Added shared volume {shared_volume}")
    else:
        logging.info("Shared volume disabled by configuration")

    return volumes


def pull_docker_image(docker_image):
    logging.info(f"Pulling docker image {docker_image}")
    try:
        docker_client.images.pull(docker_image)
    except:
        logging.critical(f"Failed to pull docker image {docker_image}")
        sys.exit(1)


def add_runner(runner, volumes, prefix, labels):
    logging.info(f"Starting runner {runner}")
    try:
        container = docker_client.containers.run(
            DOCKER_RUNNER_IMAGE,
            command="/ephemeral-runner.sh",
            volumes=volumes,
            detach=True,
            auto_remove=True,
            environment=[
                f"ACCESS_TOKEN={GITHUB_TOKEN}",
                f"RUNNER_NAME_PREFIX={prefix}",
                f"RUNNER_SCOPE=repo",
                f"REPO_URL={GITHUB_REPOSITORY_URL}",
                f"LABELS={labels}",
                f"EPHEMERAL=true",
            ],
        )
        logging.info(f"Started runner {runner} in container {container.id}")
    except:
        logging.critical(f"Failed to start runner {runner}")
        sys.exit(1)

    # monitor log files for job completion
    logs = container.logs(stream=True, follow=True)
    try:
        while True:
            line = next(logs).decode("utf-8", "ignore")
            if "completed with result" in line:
                logging.info(f"Terminating runner in container {container.id}")
                container.kill("SIGTERM")
                break
    except StopIteration:
        logging.error(
            f"End of log for container {container.id} before proper termination"
        )


def terminate_runners(signal):
    logging.info(f"Received signal {signal}, terminating runners and exiting")
    containers = docker.list()
    for container in containers:
        logging.critical(f"Terminating runner in container {container.id}")
        container.kill("SIGTERM")
    sys.exit(1)


def main():
    # setup logging
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # exit if we don't have a github token
    if not GITHUB_TOKEN:
        logging.critical("Failed to start, a GitHub token is required")
        sys.exit(1)

    # setup signal handling
    signal.signal(signal.SIGINT, terminate_runners)
    signal.signal(signal.SIGTERM, terminate_runners)

    # pull docker image
    pull_docker_image(DOCKER_RUNNER_IMAGE)

    # create volumes list
    volumes = build_volumes_list()

    # create runners in separate threads
    logging.info("Starting runners")
    for i in range(int(RUNNER_QUANTITY)):
        thread = threading.Thread(
            target=add_runner,
            kwargs={
                "runner": i,
                "volumes": volumes,
                "prefix": RUNNER_PREFIX,
                "labels": f"{RUNNER_PREFIX}-{RUN_ID},{RUNNER_LABEL}",
            },
        )
        thread.start()


if __name__ == "__main__":
    sys.exit(main())
