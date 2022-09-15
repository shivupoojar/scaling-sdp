FROM openfaas/of-watchdog:0.7.1 as watchdog

#FROM ubuntu:18.04 as build
FROM shivupoojar/aeneas-mqtt
#ARG ADDITIONAL_PKG=""
#WORKDIR /root
#RUN \
#    apt-get update && apt-get install -y \
#    autoconf \
#    build-essential \
#    libtool \
#    time \
#    bc \
#    python \
#    python-pip \
#    git

#RUN \
#    apt-get install -y \
#    wget \
#    mosquitto-clients \
#    curl 


#RUN \
#    git init && \
#    git remote add -f origin https://github.com/qub-blesson/DeFog.git && \
#    git config core.sparsecheckout true && \
#    echo Aeneas/aeneas/ >> .git/info/sparse-checkout && \
#    git pull https://github.com/qub-blesson/DeFog.git master
    
#RUN \
#    cd Aeneas/aeneas && \
#    bash install_dependencies.sh && \
#    pip install -r requirements.txt && \
#    python setup.py build_ext --inplace
#RUN pip install aeneas
#RUN apk add --no-cache python3 py3-pip
#RUN apk add make automake gcc g++ subversion python3-dev
#RUN apk add --update --no-cache g++ gcc libxml2-dev libxslt-dev python3-dev libffi-dev openssl-dev make
#RUN pip3 install numpy
#RUN apk add --no-cache ${ADDITIONAL_PKG}
#RUN apk add git
#RUN git clone https://github.com/ReadBeyond/aeneas.git
#RUN cd aeneas
#RUN pip install -r aeneas/requirements.txt
#RUN python aeneas/setup.py build_ext --inplace
#RUN pip3 install aeneas
#RUN lsof /var/lib/apt/lists/lock
#COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
#RUN chmod +x /usr/bin/fwatchdog

#RUN addgroup -S app && adduser app -S -G app
#RUN addgroup --system app && adduser app --system --ingroup app
#WORKDIR /root/

#RUN mkdir -p /home/app

# Wrapper/boot-strapper
#WORKDIR /home/app
#COPY index.sh ./

WORKDIR /home/app/function
COPY function/*.sh ./


# Copy in additional function files and folders
COPY --chown=app:app function/ .

WORKDIR /home/app/

# chmod for tmp is for a buildkit issue (@alexellis)
USER root
RUN apt-get install uuid-runtime
RUN chmod  +rx -R ./function \
    && chown app:app -R /home/app \
    && chmod 777 /tmp

USER app

ENV mode="streaming"

ENV fprocess="bash ./index.sh"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]
