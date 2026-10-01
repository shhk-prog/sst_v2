import sys
print("Python version:", sys.version)
try:
    import tensorflow as tf
    print("TensorFlow version:", tf.__version__)
    print("GPU available:", tf.config.list_physical_devices('GPU'))
except Exception as e:
    print("TensorFlow import failed:")
    import traceback
    traceback.print_exc()

try:
    import transformers
    print("Transformers version:", transformers.__version__)
    from transformers import TFAutoModelForSequenceClassification
    print("TFAutoModelForSequenceClassification import succeeded!")
except Exception as e:
    print("Transformers/TFAutoModel import failed:")
    import traceback
    traceback.print_exc()
