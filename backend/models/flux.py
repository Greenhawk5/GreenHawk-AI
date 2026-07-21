from gradio_client import Client, handle_file

from config import HF_SPACE_FLUX

from services.quota_manager import (
    get_available_token,
    consume_quota,
    disable_token
)

COLORIZATION_PROMPT = """
Colorize this black and white photograph realistically.

Preserve the original:
- composition
- objects
- faces
- textures
- details

Do not change the structure of the image.
Only add natural realistic colors.
"""


def colorize(image_path):


    attempts = 0


    while attempts < 10:


        token = get_available_token()


        print(
            "Using configured HuggingFace token"
        )


        try:


            client = Client(
                HF_SPACE_FLUX,
                token=token
            )


            result = client.predict(

                base_image=handle_file(image_path),

                reference_images=[],

                prompt=COLORIZATION_PROMPT,

                lora_prompt_text="",

                custom_prompt_text="",


                selected_titles=[],


                seed=42,

                randomize_seed=False,


                guidance_scale=3,

                steps=4,


                upscale_factor="None",


                canvas_mode="Auto (from base image)",

                custom_width=1024,

                custom_height=1024,


                canvas_fit_mode="Stretch",

                pad_color="#000000",


                batch_count=1,

                batch_vary="Random seed each run",


                sweep_min=0.4,

                sweep_max=1.4,


                param_21=1.0,
                param_22=1.0,
                param_23=1.0,
                param_24=1.0,
                param_25=1.0,
                param_26=1.0,


                api_name="/infer"
            )


            consume_quota(
                token,
                seconds=15
            )


            return result



        except Exception as error:


            print(
                "FLUX FAILED:",
                error
            )


            error_text = str(error).lower()



            if (
                "quota" in error_text
                or
                "zerogpu" in error_text
                or
                "exceeded" in error_text
            ):


                disable_token(token)


                attempts += 1


                continue



            else:

                raise error



    raise Exception(
        "All HuggingFace tokens failed"
    )
