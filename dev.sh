HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

NAME=fabfos
DOCKER_IMAGE=quay.io/hallamlab/$NAME
VER=$(cat $HERE/src/$NAME/version.txt)
echo image: $DOCKER_IMAGE:$VER
echo ""

case $1 in
    ###################################################
    # init dev environment

    -ic) # conda
        cd $HERE/envs
        mamba env create --no-default-packages -f ./dev.yml
    ;;

    ###################################################
    # build

    -bp) # pip
        # build pip package for upload to pypi
        rm -r build && rm -r dist
        python -m build --wheel
    ;;
    -bi) # pip - test install
        python setup.py install
    ;;
    -bx) # pip - remove package
        pip uninstall -y $NAME
    ;;
    -bc) # conda
        # change the url in python if not txyliu
        # build the docker container locally *with the cog db* (see above)
        docker build -t $DOCKER_IMAGE:$VER .
    ;;
    -bd) # docker
        # change the url in python if not txyliu
        # build the docker container locally *with the cog db* (see above)
        docker build -t $DOCKER_IMAGE:$VER .
    ;;
    -bs) # singularity image *from docker*
        singularity build $NAME.sif docker-daemon://$DOCKER_IMAGE:$VER
    ;;

    ###################################################
    # upload

    # -up) # pip (pypi)
    #     # login and push image to quay.io
    #     # sudo docker login quay.io
	#     docker push $DOCKER_IMAGE:$VER
    # ;;
    # -uc) # conda (personal channel)
    #     # login and push image to quay.io
    #     # sudo docker login quay.io
	#     docker push $DOCKER_IMAGE:$VER
    # ;;
    # -ud) # docker
    #     # login and push image to quay.io
    #     # sudo docker login quay.io
	#     docker push $DOCKER_IMAGE:$VER
    # ;;
    
    ###################################################
    # run

    -r)
        shift
        PYTHONPATH=$HERE/src:$PATH
        python -m $NAME $@
    ;;
    -rd) # docker
            # test run docker image
            # --mount type=bind,source="$HERE/scratch",target="/ws" \
            # --mount type=bind,source="$HERE/scratch/res",target="/ref"\
            # -e XDG_CACHE_HOME="/ws"\
            # --workdir="/ws" \
            # -u $(id -u):$(id -g) \
        shift
        docker run -it --rm $DOCKER_IMAGE:$VER /bin/bash
    ;;
    -rt) # single manual test
            # --size 20 \

        cd scratch
        python $HERE/src/FabFos.py \
            --overwrite \
            --threads 12 \
            --output ./no_miffed_test \
            --assembler megahit \
            -i --reads ./beaver_cecum_2ndhits/EKL/Raw_Data/EKL_Cecum_ligninases_pool_secondary_hits_ss01.fastq \
            -b ./ecoli_k12_mg1655.fasta \
            --pool-size 20
            # --vector ./pcc1.fasta

            # --ends ./beaver_cecum_2ndhits/endseqs.fasta \
            # --ends-name-pattern "\\w+_\\d+" \
            # --ends-fw-flag "FW" \

            # -i --reads ./beaver_cecum_2ndhits/EKL/Raw_Data/EKL_Cecum_ligninases_pool_secondary_hits_ss10.fastq \
            # --nanopore_reads beaver_cecum_2ndhits/EKL/Raw_Data/EKL_Cecum_ligninases_pool_secondary_hits_ss01.fastq \



        # scratch space for testing stuff
        #
            # --threads 14 --fabfos_path ./ --force --assembler megahit \
        # cd scratch
        # docker run -it --rm \
        #     --mount type=bind,source="./",target="/ws" \
        #     --workdir="/ws" \
        #     -u $(id -u):$(id -g) \
        #     $DOCKER_IMAGE:$VER fabfos --threads 14 --fabfos_path ./ --force --overwrite \
        #     --assembler spades_meta \
        #     --interleaved \
        #     -m miffed.csv --reads ./reads -i -b ecoli_k12_mg1655.fasta

            # --assembler spades_meta \
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
