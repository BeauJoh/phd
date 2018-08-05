FROM nvidia/cuda:9.2-runtime-ubuntu18.04
SHELL ["/bin/bash", "-c"]
RUN apt-get update
RUN apt install -y --no-install-recommends \
   ca-certificates curl g++ git libmysqlclient-dev ocl-icd-opencl-dev \
   pkg-config python python-dev python3.6 python3.6-dev python3-distutils \
   unzip zip zlib1g-dev openjdk-11-jdk
#install bazel
RUN curl -L -o /tmp/bazel.sh https://github.com/bazelbuild/bazel/releases/download/0.14.1/bazel-0.14.1-installer-linux-x86_64.sh
RUN bash /tmp/bazel.sh && rm /tmp/bazel.sh
#get and build the project
RUN git clone https://github.com/BeauJoh/phd.git
WORKDIR /phd
#install pip
RUN curl https://bootstrap.pypa.io/get-pip.py | python3
RUN pip3 install --no-cache-dir --upgrade pip
RUN ./configure --with_cuda --update_git_submodules --symlink_python --noninteractive
#install python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt
#install
RUN /bin/bash -c "source /phd/.env ;\
    export LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:$LD_LIBRARY_PATH ;\
    bazel build //deeplearning/clgen"
#run sample usage
RUN /bin/bash -c "source /phd/.env ;\
    export LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:$LD_LIBRARY_PATH ;\
    bazel run //deeplearning/clgen -- --config /phd/deeplearning/clgen/tests/data/tiny/config.pbtxt"

