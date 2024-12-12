# extract_tokenizer.py
import os
import nemo.collections.asr as nemo_asr
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_tokenizer():
    try:
        logger.info("Loading model...")
        model_path = 'model/ai4b_indicConformer_or.nemo'
        model = nemo_asr.models.EncDecCTCModelBPE.restore_from(model_path)

        logger.info("Creating tokenizer directory...")
        os.makedirs('model/tokenizer', exist_ok=True)

        logger.info("Saving tokenizer...")
        model.tokenizer.save_tokenizer('model/tokenizer')

        logger.info(f"Tokenizer files saved to model/tokenizer/")
        logger.info(f"Tokenizer files: {os.listdir('model/tokenizer')}")
    except Exception as e:
        logger.error(f"Error extracting tokenizer: {str(e)}")
        raise

if __name__ == "__main__":
    extract_tokenizer()