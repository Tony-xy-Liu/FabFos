NAME=fabfos
DOCKER_IMAGE=quay.io/hallamlab/$NAME
VER=$(cat ./src/$NAME/version.txt)
echo image: $DOCKER_IMAGE:$VER
echo ""

HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

case $1 in
    --pip-setup)
        # make an environment before hand
        # in that env, install these build tools
        pip install twine build
    ;;
    --pip-install|-i)
        # install the package locally
        python setup.py install
    ;;
    --pip-build|-b)
        # build the packge for upload to pypi
        rm -r build && rm -r dist
        python -m build --wheel
    ;;
    --pip-upload|-u)
        # upload to pypi
        # use testpypi for dev
        PYPI=testpypi
        # PYPI=pypi
        TOKEN=`cat secrets/${PYPI}`
        python -m twine upload --repository $PYPI dist/* -u __token__ -p $TOKEN
    ;;
    --pip-remove|-x)
        pip uninstall -y fabfos
    ;;
    --docker-build|-d)
        # change the url in python if not txyliu
        # build the docker container locally *with the cog db* (see above)
        docker build -t $DOCKER_IMAGE:$VER .
    ;;
    --docker-push|-p)
        # login and push image to quay.io
        # sudo docker login quay.io
	    docker push $DOCKER_IMAGE:$VER
    ;;
    --sif)
        # test build singularity
        singularity build $NAME.sif docker-daemon://$DOCKER_IMAGE:$VER
    ;;
    --run|-r)
        # test run docker image
            # --mount type=bind,source="$HERE/scratch",target="/ws" \
            # --mount type=bind,source="$HERE/scratch/res",target="/ref"\
            # -e XDG_CACHE_HOME="/ws"\
            # --workdir="/ws" \
            # -u $(id -u):$(id -g) \
        shift
        docker run -it --rm $DOCKER_IMAGE:$VER /bin/bash

    ;;
    -t)
        root=$HERE/scratch/dev_test
        out=$root/out/lake
        ws=$root/ws
        rm -r $root
            # -r /home/tony/workspace/grad/FabFos/scratch/reads/ss.fastq \
        shift
        python $HERE/src/bounce.py qc -w $ws -o $out -t 8 \
            -1 /home/tony/workspace/grad/FabFos/scratch/TEST/EKL_Cecum_ligninases_pool_secondary_hits_ss01/EKL_Cecum_ligninases_pool_secondary_hits_ss01_R1.fastq \
            -2 /home/tony/workspace/grad/FabFos/scratch/TEST/EKL_Cecum_ligninases_pool_secondary_hits_ss01/EKL_Cecum_ligninases_pool_secondary_hits_ss01_R2.fastq \
            -b /home/tony/workspace/grad/FabFos/scratch/ecoli_k12_mg1655.fasta

        # # docker
        # cd scratch
        # docker run -it --rm \
        #     --mount type=bind,source="/home/tony/workspace/grad/FabFos/src",target="/app" \
        #     --mount type=bind,source="./",target="/ws" \
        #     --workdir="/ws" \
        #     -u $(id -u):$(id -g) \
        #     $DOCKER_IMAGE:$VER fabfos --threads 14 --fabfos_path ./ --force --overwrite \
        #     --assembler megahit \
        #     --interleaved \
        #     --ends ./beaver_cecum_2ndhits/endseqs.fasta \
        #     --ends-name-pattern "\\w+_\\d+" \
        #     --ends-fw-flag "FW" \
        #     -m endseq.csv --reads ./beaver_cecum_2ndhits/EKL/Raw_Data -i -b ecoli_k12_mg1655.fasta
    ;;
    *)
        echo "bad option"
        echo $1
    ;;
esac
