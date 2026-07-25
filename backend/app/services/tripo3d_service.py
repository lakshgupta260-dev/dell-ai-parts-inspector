"""
Tripo3D / Stable-Fast-3D image-to-model service.

Uses the free Hugging Face Gradio Space (stabilityai/stable-fast-3d) as the
backend 3D generation engine — no credits, no API key required.

Flow:
  1. Call the public Gradio space with the part's front image.
  2. The space returns a path to the generated .glb file.
  3. We copy it to our uploads directory so it can be served.
"""
import os
import shutil
import logging

logger = logging.getLogger(__name__)

HF_SPACE = "stabilityai/stable-fast-3d"


def generate_3d_model(inspection_id: str, image_path: str, output_dir: str = "uploads") -> str:
    """
    Generates a 3D .glb model from *image_path* using the free
    stabilityai/stable-fast-3d Hugging Face Space via Gradio Client.

    Returns the absolute path to the saved .glb file.
    """
    try:
        from gradio_client import Client, handle_file
    except ImportError:
        raise RuntimeError(
            "gradio_client is not installed. "
            "Run: pip install gradio-client"
        )

    logger.info("[%s] Connecting to HuggingFace Space '%s'...", inspection_id, HF_SPACE)
    client = Client(HF_SPACE)

    logger.info("[%s] Submitting image for 3D generation...", inspection_id)
    result = client.predict(
        image=handle_file(image_path),
        foreground_ratio=0.85,
        api_name="/run",
    )

    # result is a tuple; the first element is the path to the generated .glb
    if isinstance(result, (list, tuple)):
        glb_tmp_path = result[0]
    else:
        glb_tmp_path = result

    if not glb_tmp_path or not os.path.exists(str(glb_tmp_path)):
        raise RuntimeError(f"HuggingFace Space returned no file: {result}")

    output_path = os.path.join(output_dir, f"{inspection_id}.glb")
    shutil.copy2(str(glb_tmp_path), output_path)
    logger.info("[%s] 3D model saved → %s", inspection_id, output_path)
    return output_path
