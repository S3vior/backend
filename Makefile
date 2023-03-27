# Set the name of the Docker image
IMAGE_NAME = savior-app

# Set the Docker command to use
DOCKER_CMD = docker

# Set the Docker run options
DOCKER_RUN_OPTS = -it --rm -p 8000:8000

# Build the Docker image
build:
	$(DOCKER_CMD) build -t $(IMAGE_NAME) .

# Run the Docker container
run:
	$(DOCKER_CMD) run $(DOCKER_RUN_OPTS) $(IMAGE_NAME)

# Clean up the Docker images
clean:
	$(DOCKER_CMD) image rm $(IMAGE_NAME)

# stop:
#     docker stop savior-app
