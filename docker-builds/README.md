Docker container to compile clgen
---------------------------------

#Dependencies

* Cuda 9.2 Runtime -- available [here](https://developer.nvidia.com/cuda-downloads)
* Docker -- available [here](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
* nvidia-docker2, install instructions found [here](https://github.com/NVIDIA/nvidia-docker)
* Docker nvidia container, installed with: `sudo apt-get install nvidia-container-runtime`

#Build

To generate a docker image named clgen-image, run:
`docker build -t clgen-instance .`

Or this can be done remotely using the latest github version with:
`docker build -t clgen-instance https://raw.githubusercontent.com/BeauJoh/phd/master/docker-builds/Dockerfile`

#Run

To start the docker image run:
`docker run --runtime=nvidia --rm -it -t clgen-instance:latest /bin/bash`
and run the demo with:
`bazel run //deeplearning/clgen -- --config /phd/deeplearning/clgen/tests/data/tiny/config.pbtxt`

