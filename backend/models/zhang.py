from gradio_client import Client, handle_file


SPACE_NAME = "Greenhawk5/AI-Colorization"


client = None



def get_client():


    global client


    if client is None:


        print(
            "Loading Zhang client..."
        )


        client = Client(
            SPACE_NAME
        )


        print(
            "Zhang client loaded"
        )


    return client



def colorize(image_path):


    client = get_client()


    result = client.predict(

        image=handle_file(image_path),

        api_name="/colorize"

    )


    return result