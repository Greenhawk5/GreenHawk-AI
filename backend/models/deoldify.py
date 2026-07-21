from gradio_client import Client, handle_file


SPACE_NAME = "leonelhs/deoldify"


client = None



def get_client():

    global client


    if client is None:

        print(
            "Loading DeOldify client..."
        )


        client = Client(
            SPACE_NAME
        )


        print(
            "DeOldify client loaded"
        )


    return client





def colorize(image_path):


    client = get_client()


    result = client.predict(

        image=handle_file(image_path),

        api_name="/predict"

    )


    if isinstance(result, dict):

        return result["path"]


    return result