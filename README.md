1. Prepare the dockerbuild and container images by running these commands in order 
```bash
cd indicasr-sagemaker
mkdir model
curl -L https://objectstore.e2enetworks.net/indic-asr-public/indicConformer/ai4b%5FindicConformer%5Fhi.nemo
-o model/ai4b_indicConformer_hi.nemo
chmod +x deploy.sh run_sagemaker_deployment.sh create_role.sh
./deploy.sh
./create_role.sh
./run_sagemaker_deployment.sh
```

2. For deleting the endpoint
```bash
python3 cleanup.py
``
